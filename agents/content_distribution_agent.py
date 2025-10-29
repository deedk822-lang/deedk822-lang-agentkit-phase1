#!/usr/bin/env python3
"""
Consumes DISTRIBUTE_CONTENT tasks from Redis, loads file, posts to real platforms.
"""
import os
import json
import yaml
import redis
import logging
import pathlib
import argparse
import requests
import tweepy
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List
from linkedin_api import Linkedin

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("distributor")

# ---------- config ----------
config_path = pathlib.Path(__file__).parent.parent / "config.yaml"
PLATFORMS = yaml.safe_load(config_path.read_text())["content_distribution"]["platforms"]

# ---------- Redis ----------
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
r = redis.from_url(REDIS_URL, decode_responses=True)

class TwitterClient:
    def __init__(self):
        api_key = os.getenv("TWITTER_API_KEY")
        api_secret = os.getenv("TWITTER_API_SECRET")
        access_token = os.getenv("TWITTER_ACCESS_TOKEN")
        access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
        
        if all([api_key, api_secret, access_token, access_token_secret]):
            auth = tweepy.OAuthHandler(api_key, api_secret)
            auth.set_access_token(access_token, access_token_secret)
            self.api = tweepy.API(auth)
            self.enabled = True
            log.info("Twitter client initialized")
        else:
            self.api = None
            self.enabled = False
            log.warning("Twitter credentials not found, posts will be simulated")
    
    def post(self, content: str) -> bool:
        if not self.enabled:
            log.info("[SIMULATED] Twitter post: %s", content[:50])
            return True
        
        try:
            # Split content if too long for Twitter
            if len(content) > 280:
                content = content[:276] + "..."
            
            tweet = self.api.update_status(content)
            log.info("Posted to Twitter: %s", tweet.id)
            return True
        except Exception as e:
            log.error("Failed to post to Twitter: %s", e)
            return False

class LinkedInClient:
    def __init__(self):
        username = os.getenv("LINKEDIN_USERNAME")
        password = os.getenv("LINKEDIN_PASSWORD")
        
        if username and password and not password.startswith("your_"):
            try:
                self.api = Linkedin(username, password)
                self.enabled = True
                log.info("LinkedIn client initialized")
            except Exception as e:
                log.warning("Failed to initialize LinkedIn client: %s", e)
                self.api = None
                self.enabled = False
        else:
            self.api = None
            self.enabled = False
            log.warning("LinkedIn credentials not found, posts will be simulated")
    
    def post(self, content: str) -> bool:
        if not self.enabled:
            log.info("[SIMULATED] LinkedIn post: %s", content[:50])
            return True
        
        try:
            self.api.add_post_update(content)
            log.info("Posted to LinkedIn successfully")
            return True
        except Exception as e:
            log.error("Failed to post to LinkedIn: %s", e)
            return False

class FacebookClient:
    def __init__(self):
        self.access_token = os.getenv("FACEBOOK_ACCESS_TOKEN")
        self.page_id = os.getenv("FACEBOOK_PAGE_ID")
        
        if self.access_token and self.page_id and not self.access_token.startswith("your_"):
            self.enabled = True
            log.info("Facebook client initialized")
        else:
            self.enabled = False
            log.warning("Facebook credentials not found, posts will be simulated")
    
    def post(self, content: str) -> bool:
        if not self.enabled:
            log.info("[SIMULATED] Facebook post: %s", content[:50])
            return True
        
        try:
            url = f"https://graph.facebook.com/v18.0/{self.page_id}/feed"
            payload = {
                'message': content,
                'access_token': self.access_token
            }
            
            response = requests.post(url, data=payload)
            if response.status_code == 200:
                result = response.json()
                log.info("Posted to Facebook: %s", result.get('id'))
                return True
            else:
                log.error("Facebook API error: %s", response.text)
                return False
        except Exception as e:
            log.error("Failed to post to Facebook: %s", e)
            return False

class RedditClient:
    def __init__(self):
        self.client_id = os.getenv("REDDIT_CLIENT_ID")
        self.client_secret = os.getenv("REDDIT_CLIENT_SECRET")
        self.username = os.getenv("REDDIT_USERNAME")
        self.password = os.getenv("REDDIT_PASSWORD")
        self.user_agent = "agentkit-phase1 by /u/" + (self.username or "unknown")
        
        if all([self.client_id, self.client_secret, self.username, self.password]) and not self.client_secret.startswith("your_"):
            try:
                import praw
                self.reddit = praw.Reddit(
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                    username=self.username,
                    password=self.password,
                    user_agent=self.user_agent
                )
                self.enabled = True
                log.info("Reddit client initialized")
            except ImportError:
                log.warning("praw not installed, Reddit posts will be simulated")
                self.enabled = False
            except Exception as e:
                log.warning("Failed to initialize Reddit client: %s", e)
                self.enabled = False
        else:
            self.enabled = False
            log.warning("Reddit credentials not found, posts will be simulated")
    
    def post(self, content: str, subreddit: str = "test") -> bool:
        if not self.enabled:
            log.info("[SIMULATED] Reddit post to r/%s: %s", subreddit, content[:50])
            return True
        
        try:
            submission = self.reddit.subreddit(subreddit).submit(
                title=content[:100] + ("..." if len(content) > 100 else ""),
                selftext=content
            )
            log.info("Posted to Reddit r/%s: %s", subreddit, submission.id)
            return True
        except Exception as e:
            log.error("Failed to post to Reddit: %s", e)
            return False

class EmailClient:
    def __init__(self):
        self.smtp_server = os.getenv("EMAIL_SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("EMAIL_SMTP_PORT", "587"))
        self.username = os.getenv("EMAIL_USERNAME")
        self.password = os.getenv("EMAIL_PASSWORD")
        self.from_email = os.getenv("EMAIL_FROM") or self.username
        
        if self.username and self.password and not self.password.startswith("your_"):
            self.enabled = True
            log.info("Email client initialized")
        else:
            self.enabled = False
            log.warning("Email credentials not found, newsletters will be simulated")
    
    def send_newsletter(self, content: str, recipients: List[str]) -> bool:
        if not self.enabled:
            log.info("[SIMULATED] Email newsletter to %d recipients: %s", len(recipients), content[:50])
            return True
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['Subject'] = "Newsletter Update"
            msg.attach(MIMEText(content, 'plain'))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                
                for recipient in recipients:
                    msg['To'] = recipient
                    server.send_message(msg)
                    del msg['To']
            
            log.info("Sent newsletter to %d recipients", len(recipients))
            return True
        except Exception as e:
            log.error("Failed to send newsletter: %s", e)
            return False

class Distributor:
    def __init__(self):
        self.clients = {
            "Twitter": TwitterClient(),
            "LinkedIn": LinkedInClient(),
            "Facebook": FacebookClient(),
            "Reddit": RedditClient(),
        }
        self.email_client = EmailClient()
        
        # Load newsletter recipients
        recipients_file = pathlib.Path(__file__).parent.parent / "newsletter_recipients.txt"
        if recipients_file.exists():
            self.newsletter_recipients = [
                line.strip() for line in recipients_file.read_text().splitlines() 
                if line.strip() and '@' in line
            ]
        else:
            self.newsletter_recipients = ["test@example.com"]
            log.warning("No newsletter_recipients.txt found, using default recipient")
    
    def distribute(self, content: str) -> Dict[str, str]:
        results = {}
        
        for platform in PLATFORMS:
            if platform == "Email Newsletter":
                success = self.email_client.send_newsletter(content, self.newsletter_recipients)
                results[platform] = "success" if success else "failed"
            elif platform in self.clients:
                success = self.clients[platform].post(content)
                results[platform] = "success" if success else "failed"
            elif platform == "Instagram":
                # Instagram requires media, simulate for now
                log.info("[SIMULATED] Instagram post: %s", content[:50])
                results[platform] = "simulated_success"
            else:
                log.warning("Unknown platform: %s", platform)
                results[platform] = "unknown_platform"
        
        return results

    def handle(self, task: Dict):
        content_file = task["params"]["content_file"]
        path = pathlib.Path(content_file)
        
        if not path.exists():
            # Try relative to project root
            path = pathlib.Path(__file__).parent.parent / content_file
        
        if not path.exists():
            log.error("Content file not found: %s", content_file)
            return
        
        try:
            content = path.read_text(encoding='utf-8')
            log.info("Distributing content from %s (%d chars)", content_file, len(content))
            
            results = self.distribute(content)
            
            # Store results in Redis for monitoring
            result_key = f"distribution_result:{task.get('id', 'unknown')}"
            r.setex(result_key, 3600, json.dumps(results))  # Expire after 1 hour
            
            log.info("Distribution complete: %s", results)
            
        except Exception as e:
            log.error("Failed to process content file %s: %s", content_file, e)

    def loop(self):
        log.info("Content distributor waiting for tasks with real platform integration...")
        while True:
            try:
                _, raw = r.brpop("agent_tasks")
                task = json.loads(raw)
                
                if task.get("type") == "DISTRIBUTE_CONTENT":
                    self.handle(task)
                else:
                    log.debug("Ignoring non-distribution task: %s", task.get("type"))
                    
            except Exception as e:
                log.error("Error processing task: %s", e)
                continue

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--content", help="Local test file (bypass Redis)")
    parser.add_argument("--test-platforms", action="store_true", help="Test all platform connections")
    args = parser.parse_args()

    distributor = Distributor()
    
    if args.test_platforms:
        test_content = "Test post from Agentkit Phase-1 🚀"
        results = distributor.distribute(test_content)
        print("Platform test results:", json.dumps(results, indent=2))
    elif args.content:
        content = pathlib.Path(args.content).read_text()
        results = distributor.distribute(content)
        print("Distribution results:", json.dumps(results, indent=2))
    else:
        distributor.loop()
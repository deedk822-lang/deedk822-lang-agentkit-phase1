#!/usr/bin/env python3
"""
Enhanced Content-Distribution Agent – Full-Cycle Integration-Lifecycle Version
------------------------------------------------------------------------------
• JSON config now a dict for platform-specific settings (e.g., API keys)
• Loads single file or whole directory of content (encourage dir mode for batch!)
• True rotating file-logger + console
• Real integrations for X and Email; simulation for others (extend easily)
• Content validation (e.g., length limits)
• Retries on send failures
• Safe error handling; argparse CLI unchanged
"""
import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import List, Dict

# ----------  logging  ----------
from logging.handlers import RotatingFileHandler
LOG = logging.getLogger("DistributionAgent")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(),
              RotatingFileHandler("distribution.log", maxBytes=5*1024*1024, backupCount=5, encoding="utf-8")]
)

# ----------  core agent  ----------
class ContentDistributionAgent:
    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self.platform_configs: Dict[str, Dict] = {}
        self.platforms: List[str] = []
        self._load_config()

    # -------------  config  -------------
    def _load_config(self) -> None:
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            self.platform_configs = cfg.get("platforms", {})
            if not isinstance(self.platform_configs, dict):
                raise ValueError("'platforms' must be a JSON object (dict)")
            self.platforms = list(self.platform_configs.keys())
            LOG.info("Platforms loaded: %s", ", ".join(self.platforms))
        except FileNotFoundError:
            LOG.error("Config file %s not found – using empty platform list", self.config_path)
            self.platform_configs = {}
        except Exception as e:
            LOG.error("Bad config file %s: %s", self.config_path, e)
            self.platform_configs = {}

    # -------------  content  -------------
    def load_content(self, source: str) -> List[str]:
        """
        If *source* is a file → return [its text].
        If *source* is a dir → return [text of each .txt file], sorted.
        TIP: Use directory mode for batch distribution to maximize capacity!
        """
        src = Path(source)
        if not src.exists():
            LOG.error("Content source %s does not exist", source)
            return []

        if src.is_file():
            try:
                return [src.read_text(encoding="utf-8")]
            except Exception as e:
                LOG.error("Cannot read %s: %s", src, e)
                return []

        # directory mode
        txt_files = sorted(src.glob("*.txt"))
        if not txt_files:
            LOG.warning("No *.txt files found in directory %s", src)
        contents = []
        for file in txt_files:
            try:
                contents.append(file.read_text(encoding="utf-8"))
            except Exception as e:
                LOG.error("Skipping %s: %s", file, e)
        LOG.info("Loaded %d content item(s) from directory %s", len(contents), src)
        return contents

    # -------------  distribution  -------------
    def distribute(self, contents: List[str]) -> None:
        if not contents:
            LOG.warning("Nothing to distribute")
            return
        if not self.platforms:
            LOG.warning("No platforms configured – nothing will be sent")
            return

        for idx, content in enumerate(contents, 1):
            LOG.info("📄 Processing content item %d/%d (%d chars)", idx, len(contents), len(content))
            for platform in self.platforms:
                config = self.platform_configs.get(platform, {})
                try:
                    self._send_to_platform(platform, content, config)
                except Exception as e:
                    LOG.error("Failed to distribute to %s: %s", platform, e)

    def _send_to_platform(self, platform: str, content: str, config: Dict) -> None:
        """
        Real API calls for supported platforms; simulation for others.
        Includes validation, retries. Extend for media by adding file params.
        TODO: For lifecycle tracking, append sent info to a 'sent.json' file.
        """
        if not config:
            LOG.warning("No config for %s – skipping", platform)
            return

        # Platform-specific validation
        if platform == "X":
            if len(content) > 280:
                content = content[:277] + "..."  # Truncate to fit
                LOG.warning("Truncated content for X to 280 chars")

        # Retry wrapper
        for attempt in range(1, 4):  # Up to 3 attempts
            try:
                if platform == "X":
                    import tweepy
                    client = tweepy.Client(
                        consumer_key=config.get('consumer_key', ''),
                        consumer_secret=config.get('consumer_secret', ''),
                        access_token=config.get('access_token', ''),
                        access_token_secret=config.get('access_token_secret', '')
                    )
                    response = client.create_tweet(text=content)
                    LOG.info("✅ Posted to X: tweet ID %s", response.data['id'])
                    return  # Success

                elif platform == "Email-Newsletter":
                    import smtplib
                    from email.mime.text import MIMEText
                    msg = MIMEText(content)
                    msg['Subject'] = config.get('subject', 'Newsletter Update')
                    msg['From'] = config.get('from_email', '')
                    msg['To'] = ", ".join(config.get('recipients', []))
                    server = smtplib.SMTP(config.get('smtp_server', ''), config.get('smtp_port', 587))
                    server.starttls()
                    server.login(config.get('username', ''), config.get('password', ''))
                    recipients = config.get('recipients', [])
                    if recipients:
                        server.sendmail(msg['From'], recipients, msg.as_string())
                        LOG.info("✅ Sent email newsletter to %d recipients", len(recipients))
                    else:
                        LOG.warning("No recipients configured for Email-Newsletter")
                    server.quit()
                    return  # Success

                else:
                    # Simulation for others (extend here, e.g., for Facebook use facebook-sdk)
                    LOG.info("✅ Simulating distribution to %s: %.60s …", platform, content)
                    return  # Simulate success

            except Exception as e:
                LOG.warning("Attempt %d failed for %s: %s", attempt, platform, e)
                if attempt == 3:
                    raise  # Final failure
                time.sleep(2 ** attempt)  # Exponential backoff

# ----------  CLI entry  ----------
def main() -> None:
    parser = argparse.ArgumentParser(description="Enhanced Content-Distribution Agent")
    parser.add_argument("--content", default="content.txt",
                        help="File or directory with content (default: content.txt)")
    parser.add_argument("--config", default="config.json",
                        help="JSON config file (default: config.json)")
    args = parser.parse_args()

    agent = ContentDistributionAgent(args.config)
    contents = agent.load_content(args.content)
    agent.distribute(contents)
    LOG.info("Distribution run complete – see distribution.log for full history")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        LOG.info("Interrupted by user – exiting gracefully")
        sys.exit(0)

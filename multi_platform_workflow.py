#!/usr/bin/env python3
"""
Automated Multi-Platform Workflow.
Distributes content across all linked accounts.
"""
import os
import pathlib
import logging
from agents.content_distribution_agent import Post, load_content, _choose_channel, _discover_services, _google_creds, _send_ayrshare, _send_google_business, _send_youtube, _send_calendar, _send_gmail

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
LOG = logging.getLogger("MultiPlatformWorkflow")

# Platform Configuration
PLATFORMS = {
    # Google Services
    "GoogleBusiness": True,
    "YouTube": True,
    "Calendar": True,
    "Gmail": True,

    # Social Media
    "TikTok": True,
    "Spotify": True,
    "WhatsApp": True,
    "Facebook": True,
    "Threads": True,
    "Bluesky": True,
    "Instagram": True,
    "Twitter": True,
    "LinkedIn": True,
    "Reddit": True,

    # Marketing & Communication
    "MailChimp": True,
    "Notion": True,
    "Slack": True,
    "Discord": True,
    "Telegram": True,

    # Other Platforms
    "iBlaze": True,
    "Medium": True,
    "Tumblr": True,
    "Pinterest": True,
    "Snapchat": True,
    "VK": True,
    "Weibo": True,
    "Line": True,
    "KakaoTalk": True
}

def distribute_to_platforms(content_dir):
    """Distribute content to all linked platforms."""
    posts = load_content(content_dir)
    if not posts:
        LOG.error("No content to distribute")
        return

    # Discover Google services
    creds, project = _google_creds()
    services = _discover_services(creds)

    # Fetch AyrShare key (fallback)
    ayr_key = ""
    try:
        from google.cloud import secretmanager
        client = secretmanager.SecretManagerServiceClient()
        ayr_key = client.access_secret_version(
            request={"name": f"projects/{project}/secrets/ayrshare-api-key/versions/latest"}
        ).payload.data.decode("UTF-8")
        LOG.info("AyrShare fallback enabled")
    except Exception as e:
        LOG.warning("AyrShare key not found: %s", e)

    for post in posts:
        # Select channel based on services and platform configuration
        channel = _choose_channel(services, post)

        # Post to selected channel
        if channel == "GoogleBusiness":
            _send_google_business(creds, post)
        elif channel == "YouTube":
            _send_youtube(creds, post)
        elif channel == "Calendar":
            _send_calendar(creds, post)
        elif channel == "Gmail":
            _send_gmail(creds, post)
        else:
            # Fallback to AyrShare for non-Google platforms
            if ayr_key:
                _send_ayrshare(ayr_key, post, PLATFORMS)
            else:
                LOG.error("AyrShare API key not available.")

if __name__ == "__main__":
    content_dir = pathlib.Path("content")  # Directory with content files
    LOG.info("Starting multi-platform distribution...")
    distribute_to_platforms(str(content_dir))
    LOG.info("Multi-platform distribution completed.")

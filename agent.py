#!/usr/bin/env python3
"""
Content-Distribution Agent – canvas-final version
------------------------------------------------------------
• JSON config for platforms (easy Jules-edit)
• Loads *either* a single file or **whole directory** of content
• Rotating file-logger + console logger
• Safe error handling everywhere
• argparse CLI so Jules can do:
    python agent.py --content ./posts/  --config jules-config.json
"""
import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import List

# ----------  logging  ----------
LOG = logging.getLogger("DistributionAgent")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(),
              logging.FileHandler("distribution.log", encoding="utf-8")]
)

# ----------  core agent  ----------
class ContentDistributionAgent:
    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self.platforms: List[str] = []
        self._load_config()

    # -------------  config  -------------
    def _load_config(self) -> None:
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            self.platforms = cfg.get("platforms", [])
            if not isinstance(self.platforms, list):
                raise ValueError("'platforms' must be a JSON list")
            LOG.info("Platforms loaded: %s", ", ".join(self.platforms))
        except FileNotFoundError:
            LOG.error("Config file %s not found – using empty platform list", self.config_path)
            self.platforms = []
        except Exception as e:
            LOG.error("Bad config file %s: %s", self.config_path, e)
            self.platforms = []

    # -------------  content  -------------
    def load_content(self, source: str) -> List[str]:
        """
        If *source* is a file → return [its text].
        If *source* is a dir → return [text of each .txt file], sorted.
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
                try:
                    self._send_to_platform(platform, content)
                except Exception as e:
                    LOG.error("Failed to distribute to %s: %s", platform, e)

    def _send_to_platform(self, platform: str, content: str) -> None:
        """
        Replace this with real API calls (Tweepy, FB-SDK, etc.).
        For Phase-1 we just *simulate*.
        """
        LOG.info("✅ Simulating distribution to %s: %.60s …", platform, content)
        # TODO: plug real APIs here
        print(f"   📤  {platform}: {content[:50]}...")

# ----------  CLI entry  ----------
def main() -> None:
    parser = argparse.ArgumentParser(description="Content-Distribution Agent")
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

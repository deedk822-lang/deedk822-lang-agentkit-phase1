#!/usr/bin/env python3
"""
Consumes DISTRIBUTE_CONTENT tasks from Redis, loads file, simulates posts.
"""
import os
import json
import yaml
import redis
import logging
import pathlib
import argparse
from typing import Dict

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("distributor")

# ---------- config ----------
PLATFORMS = yaml.safe_load(pathlib.Path("config.yaml").read_text())["content_distribution"]["platforms"]

# ---------- Redis ----------
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
r = redis.from_url(REDIS_URL, decode_responses=True)

class Distributor:
    def distribute(self, content: str) -> Dict[str, str]:
        results = {}
        for p in PLATFORMS:
            log.info("Posting to %s: %.40s...", p, content)
            results[p] = "simulated_success"
        return results

    def handle(self, task: Dict):
        path = pathlib.Path(task["params"]["content_file"])
        if not path.exists():
            log.error("File not found: %s", path)
            return
        content = path.read_text()
        res = self.distribute(content)
        log.info("Distribution done: %s", res)

    def loop(self):
        log.info("Distributor waiting for tasks …")
        while True:
            _, raw = r.brpop("agent_tasks")
            task = json.loads(raw)
            if task.get("type") == "DISTRIBUTE_CONTENT":
                self.handle(task)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--content", help="Local test file (bypass Redis)")
    args = parser.parse_args()

    if args.content:
        content = pathlib.Path(args.content).read_text()
        Distributor().distribute(content)
    else:
        Distributor().loop()
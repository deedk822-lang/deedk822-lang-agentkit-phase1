#!/usr/bin/env python3
"""
Polls a Google-Doc queue, validates commands, pushes them onto Redis bus.
"""
import os
import json
import time
import yaml
import redis
import hashlib
import logging
import pathlib
import datetime
from typing import Dict, List, Optional
from cerberus import Validator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("poller")

# ---------- config ----------
CFG_PATH = pathlib.Path(__file__).parents[1] / "config.yaml"
CFG = yaml.safe_load(CFG_PATH.read_text())["command_poller"]

# ---------- Redis ----------
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
r = redis.from_url(REDIS_URL, decode_responses=True)

# ---------- schemas ----------
SCHEMAS = {
    "SCAN_SITE": {"domain": {"type": "string", "required": True}},
    "PUBLISH_REPORT": {
        "client": {"type": "string", "required": True},
        "dataset": {"type": "string", "required": True},
        "format": {"type": "string", "required": True, "allowed": ["pdf", "csv"]},
    },
    "DISTRIBUTE_CONTENT": {"content_file": {"type": "string", "required": True}},
}

def _now() -> str:
    return datetime.datetime.utcnow().isoformat() + "Z"

def _hash(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()[:12]

def _read_doc() -> List[str]:
    path = pathlib.Path(__file__).parents[1] / "command_queue.txt"
    if not path.exists():
        path.write_text("# Add commands below\n")
    return [l.strip() for l in path.read_text().splitlines() if l.strip() and not l.startswith("#")]

class Poller:
    def __init__(self):
        self.processed: set[str] = set()

    def validate(self, raw: str) -> Optional[Dict]:
        parts = raw.split()
        cmd = parts[0].upper()
        if cmd not in SCHEMAS:
            log.warning("Unknown command: %s", cmd)
            return None
        params = {p.split("=")[0]: p.split("=")[1] for p in parts[1:] if "=" in p}
        v = Validator(SCHEMAS[cmd])
        if not v.validate(params):
            log.error("Validation failed: %s", v.errors)
            return None
        return {"type": cmd, "params": params, "raw": raw}

    def push(self, task: Dict):
        task["id"] = _hash(task["raw"])
        task["ts"] = _now()
        r.lpush("agent_tasks", json.dumps(task))
        log.info("Pushed task %s to Redis", task["id"])

    def run_once(self):
        for line in _read_doc():
            if line in self.processed:
                continue
            task = self.validate(line)
            if not task:
                continue
            self.push(task)
            self.processed.add(line)

    def run_forever(self):
        log.info("Poller started (CTRL-C to stop)")
        try:
            while True:
                self.run_once()
                time.sleep(5)
        except KeyboardInterrupt:
            log.info("Poller stopped")

if __name__ == "__main__":
    Poller().run_forever()
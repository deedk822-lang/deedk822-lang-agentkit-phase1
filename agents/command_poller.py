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
import requests
from typing import Dict, List, Optional
from cerberus import Validator
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

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
    "UPDATE_NOTION": {
        "page_id": {"type": "string", "required": True},
        "content": {"type": "string", "required": True}
    },
    "KILL_SWITCH": {},
}

def _now() -> str:
    return datetime.datetime.utcnow().isoformat() + "Z"

def _hash(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()[:12]

class GoogleDocsClient:
    def __init__(self):
        # Use service account key from environment or file
        creds_path = os.getenv("GOOGLE_CREDENTIALS_PATH")
        if creds_path and pathlib.Path(creds_path).exists():
            self.creds = Credentials.from_service_account_file(creds_path)
        else:
            # Try to use service account info from environment
            creds_info = os.getenv("GOOGLE_CREDENTIALS_JSON")
            if creds_info:
                self.creds = Credentials.from_service_account_info(json.loads(creds_info))
            else:
                log.warning("No Google credentials found, falling back to local file")
                self.creds = None
        
        if self.creds:
            self.service = build('docs', 'v1', credentials=self.creds)
        else:
            self.service = None
    
    def read_doc(self, doc_id: str) -> List[str]:
        if not self.service:
            log.warning("No Google Docs service available, using fallback")
            return self._read_fallback()
        
        try:
            doc = self.service.documents().get(documentId=doc_id).execute()
            content = doc.get('body', {}).get('content', [])
            
            commands = []
            for element in content:
                if 'paragraph' in element:
                    paragraph = element['paragraph']
                    text_run = paragraph.get('elements', [])
                    for run in text_run:
                        if 'textRun' in run:
                            text = run['textRun']['content'].strip()
                            if text and not text.startswith('#') and '=' in text:
                                commands.append(text)
            
            log.info("Read %d commands from Google Doc %s", len(commands), doc_id)
            return commands
            
        except Exception as e:
            log.error("Failed to read Google Doc %s: %s", doc_id, e)
            return self._read_fallback()
    
    def _read_fallback(self) -> List[str]:
        """Fallback to local file if Google Docs unavailable"""
        path = pathlib.Path(__file__).parents[1] / "command_queue.txt"
        if not path.exists():
            path.write_text("# Add commands below\n")
        return [l.strip() for l in path.read_text().splitlines() if l.strip() and not l.startswith("#")]

class NotionClient:
    def __init__(self):
        self.token = os.getenv("NOTION_TOKEN") or CFG.get("notion", {}).get("token")
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
    
    def update_page(self, page_id: str, content: str) -> bool:
        if not self.token or "secret_" in self.token:
            log.warning("No valid Notion token configured")
            return False
        
        try:
            url = f"https://api.notion.com/v1/pages/{page_id}"
            payload = {
                "properties": {
                    "Status": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": content
                                }
                            }
                        ]
                    }
                }
            }
            
            response = requests.patch(url, headers=self.headers, json=payload)
            if response.status_code == 200:
                log.info("Successfully updated Notion page %s", page_id)
                return True
            else:
                log.error("Failed to update Notion page: %s", response.text)
                return False
                
        except Exception as e:
            log.error("Error updating Notion page %s: %s", page_id, e)
            return False

class Poller:
    def __init__(self):
        self.processed: set[str] = set()
        self.google_client = GoogleDocsClient()
        self.notion_client = NotionClient()
        self.kill_switch_active = False
    
    def check_kill_switch(self) -> bool:
        """Check Redis for kill switch signal"""
        kill_key = CFG.get("kill_switch_key", "agentkit_kill_switch")
        if r.get(kill_key):
            log.warning("Kill switch activated!")
            self.kill_switch_active = True
            return True
        return False

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

    def execute_command(self, task: Dict):
        """Execute commands directly instead of just queuing them"""
        cmd_type = task["type"]
        params = task["params"]
        
        if cmd_type == "UPDATE_NOTION":
            success = self.notion_client.update_page(params["page_id"], params["content"])
            if success:
                log.info("Executed UPDATE_NOTION successfully")
            else:
                log.error("Failed to execute UPDATE_NOTION")
        
        elif cmd_type == "KILL_SWITCH":
            kill_key = CFG.get("kill_switch_key", "agentkit_kill_switch")
            r.set(kill_key, "active")
            log.warning("Kill switch activated via command")
            self.kill_switch_active = True
        
        else:
            # Queue other commands for agents to process
            self.push_to_queue(task)
    
    def push_to_queue(self, task: Dict):
        task["id"] = _hash(task["raw"])
        task["ts"] = _now()
        r.lpush("agent_tasks", json.dumps(task))
        log.info("Pushed task %s to Redis queue", task["id"])

    def run_once(self):
        if self.check_kill_switch():
            return
        
        # Read from Google Docs
        doc_id = os.getenv("GOOGLE_DOC_ID") or CFG.get("google_doc_id")
        commands = self.google_client.read_doc(doc_id)
        
        for line in commands:
            if line in self.processed:
                continue
            task = self.validate(line)
            if not task:
                continue
            self.execute_command(task)
            self.processed.add(line)

    def run_forever(self):
        log.info("Poller started with Google Docs integration (CTRL-C to stop)")
        try:
            while True:
                if self.kill_switch_active:
                    log.warning("Shutting down due to kill switch")
                    break
                self.run_once()
                time.sleep(5)
        except KeyboardInterrupt:
            log.info("Poller stopped")

if __name__ == "__main__":
    Poller().run_forever()
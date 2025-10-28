import json
import os
from datetime import datetime

class NotionKVClient:
    def __init__(self, token):
        # In a real scenario, this would use the token to connect to the Notion API.
        self.ledger_path = "server/ledger.txt"
        if not os.path.exists(os.path.dirname(self.ledger_path)):
            os.makedirs(os.path.dirname(self.ledger_path))

    def append_ledger(self, **kwargs):
        """Appends a new record to the ledger file."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "data": kwargs
        }
        with open(self.ledger_path, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
        print(f"Appended to ledger: {kwargs.get('subject')}")

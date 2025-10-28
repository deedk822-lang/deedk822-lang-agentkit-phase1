import json
import os
from agents.a2a_marketplace import redis_client, RESULTS_CHANNEL
# Re-use your existing Notion client
from notion_client.client import NotionKVClient

AGENT_NAME = "AuditorAgent"
NOTION_TOKEN = os.getenv("NOTION_TOKEN", "your-notion-token")

class AuditorAgent:
    def __init__(self):
        self.notion_client = NotionKVClient(NOTION_TOKEN)
        self.pubsub = redis_client.pubsub(ignore_subscribe_messages=True)
        self.pubsub.subscribe(RESULTS_CHANNEL)
        print(f"[{AGENT_NAME}] Subscribed to results channel. Awaiting job completion events...")

    def run(self):
        for message in self.pubsub.listen():
            result = json.loads(message['data'])
            job_id = result['job_id']
            status = result['status']
            completed_by = result['completed_by']

            print(f"[{AGENT_NAME}] Observed result for job {job_id} by {completed_by}. Status: {status}")

            # Here, we record the result in our tamper-evident ledger
            self.notion_client.append_ledger(
                action_id=job_id,
                subject=f"A2A Task Completion by {completed_by}",
                result=status,
                latency_ms=0, # Latency would be calculated if we stored start times
                signed_by=AGENT_NAME,
                rationale=json.dumps(result['result_data'])
            )

if __name__ == "__main__":
    agent = AuditorAgent()
    agent.run()

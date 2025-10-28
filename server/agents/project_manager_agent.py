import redis
import time
import os
from command_poller.poller import GoogleDocClient, CommandParser, CommandType
from agents.a2a_marketplace import post_task

AGENT_NAME = "ProjectManagerAgent"
GOOGLE_DOC_ID = os.getenv("GOOGLE_DOC_ID", "your-doc-id-from-env")

class ProjectManagerAgent:
    def __init__(self):
        self.doc_client = GoogleDocClient(GOOGLE_DOC_ID)
        self.processed_lines = set()

    def run(self):
        print(f"[{AGENT_NAME}] Starting up. Monitoring command file...")
        while True:
            lines = self.doc_client.read_commands()
            for line_num, line in enumerate(lines, 1):
                if line in self.processed_lines:
                    continue

                parsed = CommandParser.parse_line(line, line_num)
                if parsed and parsed.command_type != CommandType.UNKNOWN:
                    print(f"[{AGENT_NAME}] Detected new command: {parsed.raw_text}")
                    # The manager now posts a task for any recognized command.
                    post_task(
                        task_type=parsed.command_type.value,
                        params=parsed.params,
                        posted_by=AGENT_NAME
                    )
                    self.processed_lines.add(line)

            time.sleep(10) # Polls every 10 seconds

if __name__ == "__main__":
    agent = ProjectManagerAgent()
    agent.run()

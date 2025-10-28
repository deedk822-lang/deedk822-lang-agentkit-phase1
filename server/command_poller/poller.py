import re
from collections import namedtuple
from enum import Enum

class CommandType(Enum):
    START_CAMPAIGN = "START_CAMPAIGN"
    REFACTOR_CODE = "REFACTOR_CODE"
    PROVISION_INFRA = "PROVISION_INFRA"
    UNKNOWN = "UNKNOWN"

ParsedCommand = namedtuple('ParsedCommand', ['raw_text', 'command_type', 'params'])

class GoogleDocClient:
    def __init__(self, doc_id):
        # In a real scenario, this would use the doc_id to connect to the Google Docs API.
        # For this example, we'll read from a local file.
        self.doc_path = "server/dummy_doc.txt"

    def read_commands(self):
        """Reads lines from the dummy doc file."""
        try:
            with open(self.doc_path, 'r') as f:
                return [line.strip() for line in f.readlines()]
        except FileNotFoundError:
            print(f"Error: Command file not found at {self.doc_path}")
            return []

class CommandParser:
    @staticmethod
    def parse_line(line, line_num):
        """Parses a line into a command and its parameters."""
        if not line or line.startswith('#'):
            return None

        match = re.match(r'(\w+):\s*(.*)', line)
        if not match:
            return None

        command_str, params_str = match.groups()
        try:
            command_type = CommandType(command_str.upper())
        except ValueError:
            command_type = CommandType.UNKNOWN

        params = {}
        if params_str:
            param_pairs = [p.strip() for p in params_str.split(',')]
            for pair in param_pairs:
                if '=' in pair:
                    key, value = pair.split('=', 1)
                    params[key.strip()] = value.strip()

        return ParsedCommand(raw_text=line, command_type=command_type, params=params)

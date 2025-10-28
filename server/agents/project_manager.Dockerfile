FROM python:3.11-slim
WORKDIR /app

# 1. Install dependencies
COPY server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2. Create directories for python packages
RUN mkdir -p /app/agents /app/command_poller

# 3. Copy application code
COPY server/agents/project_manager_agent.py /app/agents/
COPY server/agents/a2a_marketplace.py /app/agents/
COPY server/command_poller/poller.py /app/command_poller/

# 4. Create __init__.py to make them packages
RUN touch /app/agents/__init__.py
RUN touch /app/command_poller/__init__.py

# 5. Define the command to run the application
CMD ["python", "-m", "agents.project_manager_agent"]

FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY ./agents /app/agents
COPY ./command_poller /app/command_poller # Needs the parser
CMD ["python", "agents/project_manager_agent.py"]

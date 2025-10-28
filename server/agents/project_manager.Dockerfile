FROM python:3.11-slim
WORKDIR /app
COPY server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY ./server/agents /app/agents
COPY ./server/command_poller /app/command_poller # Needs the parser
CMD ["python", "agents/project_manager_agent.py"]

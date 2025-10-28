FROM python:3.11-slim
WORKDIR /app
COPY server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY ./server/agents /app/agents
COPY ./server/notion_client /app/notion_client # Needs the Notion client
CMD ["python", "agents/auditor_agent.py"]

FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY ./agents /app/agents
COPY ./notion_client /app/notion_client # Needs the Notion client
CMD ["python", "agents/auditor_agent.py"]

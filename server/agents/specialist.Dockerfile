FROM python:3.11-slim
WORKDIR /app
COPY server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY ./server/agents /app/agents
COPY ./server/integrations /app/integrations
CMD ["python", "agents/specialist_agents.py"]

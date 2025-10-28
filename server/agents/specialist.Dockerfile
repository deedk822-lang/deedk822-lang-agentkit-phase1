FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY ./agents /app/agents
CMD ["python", "agents/specialist_agents.py"]

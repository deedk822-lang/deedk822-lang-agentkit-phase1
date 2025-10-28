import json
import os
import uuid
from typing import Dict, Optional
import redis

# Connect to Redis using the URL provided by Kubernetes
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

TASK_QUEUE = "agent_tasks"
RESULTS_CHANNEL = "agent_results"

def post_task(task_type: str, params: Dict, posted_by: str) -> str:
    """Posts a new job to the central task queue."""
    job_id = str(uuid.uuid4())
    job = {
        "job_id": job_id,
        "task_type": task_type,
        "params": params,
        "status": "PENDING",
        "posted_by": posted_by
    }
    redis_client.lpush(TASK_QUEUE, json.dumps(job))
    print(f"[{posted_by}] Posted new task {task_type} with job_id: {job_id}")
    return job_id

def claim_task() -> Optional[Dict]:
    """Atomically claims a task from the queue."""
    # BRPOP is a blocking pop, it will wait for a task to appear.
    # The timeout prevents it from waiting forever.
    task_json = redis_client.brpop(TASK_QUEUE, timeout=30)
    if task_json:
        return json.loads(task_json[1])
    return None

def publish_result(job_id: str, status: str, result_data: Dict, completed_by: str):
    """Publishes the result of a completed job to the results channel."""
    result = {
        "job_id": job_id,
        "status": status,
        "result_data": result_data,
        "completed_by": completed_by
    }
    redis_client.publish(RESULTS_CHANNEL, json.dumps(result))
    print(f"[{completed_by}] Published result for job_id: {job_id} with status: {status}")

import time
import random
from agents.a2a_marketplace import claim_task, publish_result

AGENT_NAME = "SpecialistAgent"

def simulate_start_campaign(params):
    """Simulates starting a marketing campaign."""
    print(f"[{AGENT_NAME}/Marketing] Starting campaign {params.get('campaign_id')}...")
    time.sleep(random.uniform(2, 5)) # Simulate work
    return {"status": "SUCCESS", "confirmation_code": "CAMPAIGN_STARTED"}

def simulate_code_refactor(params):
    """Simulates a code refactoring task."""
    print(f"[{AGENT_NAME}/CodeRefactor] Starting refactor for {params.get('target')}...")
    time.sleep(random.uniform(3, 7)) # Simulate work
    return {"status": "SUCCESS", "new_code_path": "/path/to/refactored/code.py"}

def simulate_infra_provisioning(params):
    """Simulates a cloud provisioning task."""
    print(f"[{AGENT_NAME}/CloudProvisioner] Starting to provision {params.get('service')}...")
    time.sleep(random.uniform(5, 10)) # Simulate work
    return {"status": "SUCCESS", "service_ip": "34.123.45.67"}

def run():
    print(f"[{AGENT_NAME}] Worker is online. Waiting for tasks on the marketplace...")
    while True:
        task = claim_task()
        if task:
            job_id = task['job_id']
            task_type = task['task_type']
            params = task['params']

            result_data = {}
            status = "FAILED"
            handler = None

            # Agent decides if it has the skill for the job
            if task_type == "START_CAMPAIGN":
                handler = simulate_start_campaign
            elif task_type == "REFACTOR_CODE":
                handler = simulate_code_refactor
            elif task_type == "PROVISION_INFRA":
                handler = simulate_infra_provisioning

            if handler:
                result_data = handler(params)
                status = "SUCCESS"
            else:
                print(f"[{AGENT_NAME}] Skipping task of unknown type: {task_type}")
                continue # Get next task

            publish_result(job_id, status, result_data, AGENT_NAME)

if __name__ == "__main__":
    run()

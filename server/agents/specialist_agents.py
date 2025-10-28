import time
import random
from agents.a2a_marketplace import claim_task, publish_result
from integrations.mailchimp_agent import check_integration, refresh_token, create_audience_sync

AGENT_NAME = "SpecialistAgent"

# --- Simulation stubs for non-Mailchimp tasks ---
def simulate_start_campaign(params):
    print(f"[{AGENT_NAME}/Marketing] Starting campaign {params.get('campaign_id')}...")
    time.sleep(random.uniform(2, 5))
    return {"status": "SUCCESS", "confirmation_code": "CAMPAIGN_STARTED"}

def simulate_code_refactor(params):
    print(f"[{AGENT_NAME}/CodeRefactor] Starting refactor for {params.get('target')}...")
    time.sleep(random.uniform(3, 7))
    return {"status": "SUCCESS", "new_code_path": "/path/to/refactored/code.py"}

def simulate_infra_provisioning(params):
    print(f"[{AGENT_NAME}/CloudProvisioner] Starting to provision {params.get('service')}...")
    time.sleep(random.uniform(5, 10))
    return {"status": "SUCCESS", "service_ip": "34.123.45.67"}

def simulate_connect_integration(params):
    print(f"[{AGENT_NAME}/IntegrationManager] Connecting {params.get('service')}...")
    time.sleep(random.uniform(4, 8))
    # This would involve a complex OAuth flow in reality
    return {"status": "SUCCESS", "connection_status": "connected_via_oauth"}

def simulate_distribute_content(params):
    print(f"[{AGENT_NAME}/ContentDistributor] Distributing content from {params.get('content_dir')}...")
    time.sleep(random.uniform(3, 6))
    return {"status": "SUCCESS", "distribution_report": "all platforms successful"}

# --- Main task execution loop ---
def run():
    print(f"[{AGENT_NAME}] Worker is online. Waiting for tasks...")
    while True:
        task = claim_task()
        if not task:
            continue

        job_id = task['job_id']
        task_type = task['task_type']
        params = task['params']

        result_data = {}
        status = "FAILED"
        handler = None

        # Map task types to handlers (real or simulated)
        handlers = {
            "START_CAMPAIGN": simulate_start_campaign,
            "REFACTOR_CODE": simulate_code_refactor,
            "PROVISION_INFRA": simulate_infra_provisioning,
            "CONNECT_INTEGRATION": simulate_connect_integration,
            "DISTRIBUTE_CONTENT": simulate_distribute_content,
            # --- Real Mailchimp integration handlers ---
            "CHECK_INTEGRATION_STATUS": lambda p: check_integration(p['service']),
            "REFRESH_TOKEN": lambda p: refresh_token(p['service']),
            "SYNC_AUDIENCE": lambda p: create_audience_sync(p['audience_id'], p['dest_platform']),
        }

        handler = handlers.get(task_type)

        if handler:
            try:
                print(f"[{AGENT_NAME}] Handling task: {task_type} with params: {params}")
                result_data = handler(params)
                status = "SUCCESS"
            except Exception as e:
                print(f"[{AGENT_NAME}] Error handling {task_type}: {e}")
                # Check for Mailchimp API key error specifically
                if "MAILCHIMP_API_KEY" in str(e):
                    result_data = {"error": "Mailchimp API key not configured."}
                else:
                    result_data = {"error": str(e)}
        else:
            print(f"[{AGENT_NAME}] Skipping task of unknown type: {task_type}")
            continue

        publish_result(job_id, status, result_data, AGENT_NAME)

if __name__ == "__main__":
    run()

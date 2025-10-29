# Agentkit Phase 1 – Production Control Plane

Cloud-native automation system that polls commands from a Google-Doc queue,
validates them, and executes via containerised agents on GKE.

## Quick start
```bash
bash setup.sh                 # creates venv + pip install
source venv/bin/activate
pytest tests/ -v              # 3 green tests
python -m agents.command_poller &        # terminal 1
python -m agents.content_distribution_agent  # terminal 2
```

Deploy to GKE
1. Replace `YOUR_GCP_PROJECT` inside `k8s/gcp-deployment.yml`
2. `kubectl apply -f k8s/gcp-deployment.yml`
3. Push to `main` – GitHub Actions builds & rolls out automatically.
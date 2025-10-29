# AgentKit Phase-1 GKE Deployment Guide

## Step 1: Replace Kubernetes Deployment File

**Action:** Replace the content of `k8s/gcp-deployment.yml` with the complete manifest I provided above.

```bash
# Backup old file
mv k8s/gcp-deployment.yml k8s/gcp-deployment.yml.backup

# Copy the new complete manifest
# (Use the artifact "Complete GKE Deployment Manifest" I just created)
```

---

## Step 2: Create GKE Cluster

If you don't have a GKE cluster yet, create one:

```bash
# Set your project
export PROJECT_ID="your-project-id"
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable container.googleapis.com \
  artifactregistry.googleapis.com \
  iamcredentials.googleapis.com

# Create GKE cluster
gcloud container clusters create agentkit-cluster \
  --zone=us-central1-a \
  --num-nodes=3 \
  --machine-type=e2-medium \
  --disk-size=30 \
  --enable-autoscaling \
  --min-nodes=2 \
  --max-nodes=5

# Get cluster credentials
gcloud container clusters get-credentials agentkit-cluster --zone=us-central1-a
```

---

## Step 3: Set Up Workload Identity Federation (WIF)

### 3.1 Create Workload Identity Pool

```bash
export PROJECT_ID="your-project-id"
export PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
export GITHUB_REPO="deedk822-lang/deedk822-lang-agentkit-phase1"

# Create pool
gcloud iam workload-identity-pools create "github-pool" \
  --project="${PROJECT_ID}" \
  --location="global" \
  --display-name="GitHub Actions Pool"
```

### 3.2 Create WIF Provider

```bash
# Create provider
gcloud iam workload-identity-pools providers create-oidc "github-provider" \
  --project="${PROJECT_ID}" \
  --location="global" \
  --workload-identity-pool="github-pool" \
  --display-name="GitHub Provider" \
  --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository,attribute.repository_owner=assertion.repository_owner" \
  --issuer-uri="https://token.actions.githubusercontent.com"
```

### 3.3 Get WIF_PROVIDER Value

```bash
# Get the full provider name (this is your WIF_PROVIDER secret)
gcloud iam workload-identity-pools providers describe "github-provider" \
  --project="${PROJECT_ID}" \
  --location="global" \
  --workload-identity-pool="github-pool" \
  --format="value(name)"
```

**Copy the output** - it looks like:
```
projects/123456789/locations/global/workloadIdentityPools/github-pool/providers/github-provider
```

---

## Step 4: Create Service Account

### 4.1 Create the Service Account

```bash
# Create service account
gcloud iam service-accounts create github-actions-sa \
  --project="${PROJECT_ID}" \
  --display-name="GitHub Actions Service Account"

# Get service account email
export SA_EMAIL="github-actions-sa@${PROJECT_ID}.iam.gserviceaccount.com"
```

### 4.2 Grant Permissions

```bash
# GCR push permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/storage.admin"

# GKE deployment permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/container.developer"

# Allow GitHub to impersonate this service account
gcloud iam service-accounts add-iam-policy-binding "${SA_EMAIL}" \
  --project="${PROJECT_ID}" \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/github-pool/attribute.repository/${GITHUB_REPO}"
```

---

## Step 5: Configure GitHub Secrets

Go to your GitHub repository:
**Settings â†’ Secrets and variables â†’ Actions â†’ New repository secret**

Add these secrets:

| Secret Name | Value | How to Get It |
|-------------|-------|---------------|
| `GCP_PROJECT_ID` | Your GCP project ID | `echo $PROJECT_ID` |
| `WIF_PROVIDER` | Full WIF provider path | From Step 3.3 |
| `WIF_SERVICE_ACCOUNT` | Service account email | `echo $SA_EMAIL` |
| `GKE_CLUSTER_NAME` | `agentkit-cluster` | Name you used in Step 2 |
| `GKE_CLUSTER_ZONE` | `us-central1-a` | Zone you used in Step 2 |

---

## Step 6: Uncomment Deployment Job

Edit `.github/workflows/deploy.yml` and uncomment lines 87-148:

**Before:**
```yaml
  # deploy-to-gcp:
  #   runs-on: ubuntu-latest
```

**After:**
```yaml
  deploy-to-gcp:
    runs-on: ubuntu-latest
```

**Remove the `#` from EVERY line** in that section (lines 87-148).

---

## Step 7: Create Kubernetes Secrets

Before deploying, create secrets for your API keys:

```bash
# Create namespace first
kubectl create namespace agentkit

# Create secret (replace with your actual values)
kubectl create secret generic agentkit-secrets \
  --namespace=agentkit \
  --from-literal=REDIS_URL='redis://redis:6379/0' \
  --from-literal=GOOGLE_DOC_ID='your-google-doc-id' \
  --from-literal=GOOGLE_CREDENTIALS_JSON='{"type":"service_account",...}' \
  --from-literal=TWITTER_API_KEY='your-key' \
  --from-literal=TWITTER_API_SECRET='your-secret' \
  --from-literal=TWITTER_ACCESS_TOKEN='your-token' \
  --from-literal=TWITTER_ACCESS_TOKEN_SECRET='your-token-secret' \
  --from-literal=LINKEDIN_USERNAME='your-username' \
  --from-literal=LINKEDIN_PASSWORD='your-password' \
  --from-literal=FACEBOOK_ACCESS_TOKEN='your-token' \
  --from-literal=FACEBOOK_PAGE_ID='your-page-id' \
  --from-literal=REDDIT_CLIENT_ID='your-client-id' \
  --from-literal=REDDIT_CLIENT_SECRET='your-secret' \
  --from-literal=REDDIT_USERNAME='your-username' \
  --from-literal=REDDIT_PASSWORD='your-password' \
  --from-literal=EMAIL_USERNAME='your-email' \
  --from-literal=EMAIL_PASSWORD='your-app-password' \
  --from-literal=EMAIL_FROM='your-email' \
  --from-literal=NOTION_TOKEN='your-notion-token'
```

Or create from a file:

```bash
# Create a secrets.env file
cat > secrets.env << EOF
REDIS_URL=redis://redis:6379/0
GOOGLE_DOC_ID=your-google-doc-id
GOOGLE_CREDENTIALS_JSON={"type":"service_account",...}
TWITTER_API_KEY=your-key
# ... add all your secrets
EOF

# Create secret from file
kubectl create secret generic agentkit-secrets \
  --namespace=agentkit \
  --from-env-file=secrets.env

# Clean up
rm secrets.env
```

---

## Step 8: Deploy!

### Option A: Deploy via GitHub Actions

```bash
# Commit and push your changes
git add k8s/gcp-deployment.yml .github/workflows/deploy.yml
git commit -m "Enable GKE deployment"
git push origin main
```

The workflow will automatically:
1. Build all 4 Docker images
2. Push them to GCR
3. Deploy to your GKE cluster

### Option B: Deploy Manually

```bash
# Build and push images locally
export REGISTRY="gcr.io/${PROJECT_ID}"

docker build -f Dockerfile.poller -t ${REGISTRY}/agentkit-command-poller:latest .
docker build -f Dockerfile.distributor -t ${REGISTRY}/agentkit-content-distribution:latest .
docker build -f Dockerfile.scanner -t ${REGISTRY}/agentkit-site-scanner:latest .
docker build -f Dockerfile.reports -t ${REGISTRY}/agentkit-report-generator:latest .

# Push to GCR
gcloud auth configure-docker
docker push ${REGISTRY}/agentkit-command-poller:latest
docker push ${REGISTRY}/agentkit-content-distribution:latest
docker push ${REGISTRY}/agentkit-site-scanner:latest
docker push ${REGISTRY}/agentkit-report-generator:latest

# Deploy to GKE
export GCP_PROJECT_ID=$PROJECT_ID
envsubst < k8s/gcp-deployment.yml | kubectl apply -f -
```

---

## Step 9: Verify Deployment

```bash
# Check namespace
kubectl get namespaces

# Check all resources
kubectl get all -n agentkit

# Check pods status
kubectl get pods -n agentkit

# Check logs
kubectl logs -n agentkit deployment/command-poller
kubectl logs -n agentkit deployment/content-distribution
kubectl logs -n agentkit deployment/site-scanner
kubectl logs -n agentkit deployment/report-generator

# Check Redis
kubectl exec -n agentkit deployment/redis -- redis-cli ping
```

---

## Step 10: Test the System

### Add a test command to your Google Doc or command_queue.txt:

```
SCAN_SITE domain=example.com
```

### Watch the logs:

```bash
# Command poller
kubectl logs -f -n agentkit deployment/command-poller

# Site scanner
kubectl logs -f -n agentkit deployment/site-scanner
```

---

## Troubleshooting

### Pods not starting?

```bash
# Describe pod to see events
kubectl describe pod -n agentkit <pod-name>

# Check events
kubectl get events -n agentkit --sort-by='.lastTimestamp'
```

### Image pull errors?

```bash
# Make sure GCR permissions are correct
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/storage.objectViewer"
```

### Redis connection issues?

```bash
# Check Redis is running
kubectl get pods -n agentkit -l app=redis

# Test Redis connection from a pod
kubectl exec -n agentkit deployment/command-poller -- \
  python -c "import redis; r=redis.from_url('redis://redis:6379/0'); print(r.ping())"
```

---

## Monitoring & Management

### Scale deployments:

```bash
kubectl scale deployment/content-distribution --replicas=2 -n agentkit
```

### Update images:

```bash
kubectl set image deployment/command-poller \
  poller=gcr.io/${PROJECT_ID}/agentkit-command-poller:new-tag \
  -n agentkit
```

### Restart a deployment:

```bash
kubectl rollout restart deployment/command-poller -n agentkit
```

---

## Cleanup

To delete everything:

```bash
# Delete all resources
kubectl delete namespace agentkit

# Delete GKE cluster
gcloud container clusters delete agentkit-cluster --zone=us-central1-a
```

---

## Summary Checklist

- [ ] Replace `k8s/gcp-deployment.yml` with complete manifest
- [ ] Create GKE cluster
- [ ] Set up Workload Identity Federation
- [ ] Create and configure service account
- [ ] Add GitHub secrets
- [ ] Uncomment deployment job in workflow
- [ ] Create Kubernetes secrets for API keys
- [ ] Commit and push changes
- [ ] Verify deployment
- [ ] Test with sample commands

**Your AgentKit system is now production-ready! ðŸš€**
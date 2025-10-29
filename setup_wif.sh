#!/bin/bash
# Complete Workload Identity Federation Setup Script for AgentKit
# This script sets up everything needed for GitHub Actions to deploy to GKE

set -e  # Exit on error

echo "🚀 AgentKit Workload Identity Federation Setup"
echo "=============================================="
echo ""

# ============================================
# STEP 1: Set your project details
# ============================================
read -p "Enter your GCP Project ID: " PROJECT_ID
read -p "Enter your GitHub repository (format: username/repo-name): " GITHUB_REPO

if [ -z "$PROJECT_ID" ] || [ -z "$GITHUB_REPO" ]; then
    echo "❌ Error: Project ID and GitHub repo are required"
    exit 1
fi

echo ""
echo "📋 Configuration:"
echo "   Project ID: $PROJECT_ID"
echo "   GitHub Repo: $GITHUB_REPO"
echo ""

# Set the project
gcloud config set project $PROJECT_ID

# Get project number
export PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
echo "   Project Number: $PROJECT_NUMBER"
echo ""

# ============================================
# STEP 2: Enable required APIs
# ============================================
echo "🔧 Enabling required Google Cloud APIs..."
gcloud services enable \
    iamcredentials.googleapis.com \
    container.googleapis.com \
    storage-api.googleapis.com \
    sts.googleapis.com \
    cloudresourcemanager.googleapis.com

echo "✅ APIs enabled"
echo ""

# ============================================
# STEP 3: Create Workload Identity Pool
# ============================================
echo "🏊 Creating Workload Identity Pool..."

# Check if pool already exists
if gcloud iam workload-identity-pools describe "github-pool" \
    --project="${PROJECT_ID}" \
    --location="global" &> /dev/null; then
    echo "⚠️  Pool 'github-pool' already exists, skipping creation"
else
    gcloud iam workload-identity-pools create "github-pool" \
        --project="${PROJECT_ID}" \
        --location="global" \
        --display-name="GitHub Actions Pool"
    echo "✅ Workload Identity Pool created"
fi
echo ""

# ============================================
# STEP 4: Create Workload Identity Provider
# ============================================
echo "🔐 Creating Workload Identity Provider..."

# Check if provider already exists
if gcloud iam workload-identity-pools providers describe "github-provider" \
    --project="${PROJECT_ID}" \
    --location="global" \
    --workload-identity-pool="github-pool" &> /dev/null; then
    echo "⚠️  Provider 'github-provider' already exists, skipping creation"
else
    gcloud iam workload-identity-pools providers create-oidc "github-provider" \
        --project="${PROJECT_ID}" \
        --location="global" \
        --workload-identity-pool="github-pool" \
        --display-name="GitHub Provider" \
        --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository,attribute.repository_owner=assertion.repository_owner" \
        --attribute-condition="assertion.repository=='${GITHUB_REPO}'" \
        --issuer-uri="https://token.actions.githubusercontent.com"
    echo "✅ Workload Identity Provider created"
fi
echo ""

# ============================================
# STEP 5: Get WIF Provider full name
# ============================================
echo "📝 Getting Workload Identity Provider details..."
WIF_PROVIDER=$(gcloud iam workload-identity-pools providers describe "github-provider" \
    --project="${PROJECT_ID}" \
    --location="global" \
    --workload-identity-pool="github-pool" \
    --format="value(name)")

echo "✅ WIF Provider: $WIF_PROVIDER"
echo ""

# ============================================
# STEP 6: Create Service Account
# ============================================
echo "👤 Creating Service Account..."

SA_NAME="github-actions-sa"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

# Check if service account already exists
if gcloud iam service-accounts describe "${SA_EMAIL}" \
    --project="${PROJECT_ID}" &> /dev/null; then
    echo "⚠️  Service account '${SA_EMAIL}' already exists, skipping creation"
else
    gcloud iam service-accounts create "${SA_NAME}" \
        --project="${PROJECT_ID}" \
        --display-name="GitHub Actions Service Account" \
        --description="Service account for GitHub Actions deployments"
    echo "✅ Service Account created: ${SA_EMAIL}"
fi
echo ""

# ============================================
# STEP 7: Grant IAM Permissions
# ============================================
echo "🔑 Granting IAM permissions to service account..."

# Storage Admin (for GCR)
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/storage.admin" \
    --condition=None

# Container Developer (for GKE)
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/container.developer" \
    --condition=None

# Allow GitHub to impersonate this service account
gcloud iam service-accounts add-iam-policy-binding "${SA_EMAIL}" \
    --project="${PROJECT_ID}" \
    --role="roles/iam.workloadIdentityUser" \
    --member="principalSet://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/github-pool/attribute.repository/${GITHUB_REPO}"

echo "✅ IAM permissions granted"
echo ""

# ============================================
# STEP 8: Create or verify GKE cluster
# ============================================
echo "☸️  Checking for GKE cluster..."

read -p "Do you want to create a new GKE cluster? (y/n): " CREATE_CLUSTER

if [ "$CREATE_CLUSTER" = "y" ] || [ "$CREATE_CLUSTER" = "Y" ]; then
    read -p "Enter cluster name (default: agentkit-cluster): " CLUSTER_NAME
    CLUSTER_NAME=${CLUSTER_NAME:-agentkit-cluster}

    read -p "Enter cluster zone (default: us-central1-a): " CLUSTER_ZONE
    CLUSTER_ZONE=${CLUSTER_ZONE:-us-central1-a}

    echo "Creating GKE cluster '$CLUSTER_NAME' in zone '$CLUSTER_ZONE'..."

    gcloud container clusters create $CLUSTER_NAME \
        --zone=$CLUSTER_ZONE \
        --num-nodes=3 \
        --machine-type=e2-medium \
        --disk-size=30 \
        --enable-autoscaling \
        --min-nodes=2 \
        --max-nodes=5 \
        --enable-autorepair \
        --enable-autoupgrade

    echo "✅ GKE cluster created: $CLUSTER_NAME"
else
    read -p "Enter existing cluster name: " CLUSTER_NAME
    read -p "Enter cluster zone: " CLUSTER_ZONE
    echo "✅ Using existing cluster: $CLUSTER_NAME"
fi

echo ""

# ============================================
# STEP 9: Get cluster credentials
# ============================================
echo "🔧 Getting cluster credentials..."
gcloud container clusters get-credentials $CLUSTER_NAME --zone=$CLUSTER_ZONE
echo "✅ Cluster credentials configured"
echo ""

# ============================================
# STEP 10: Summary and Next Steps
# ============================================
echo ""
echo "🎉 ============================================"
echo "🎉 SETUP COMPLETE!"
echo "🎉 ============================================"
echo ""
echo "📋 GitHub Secrets to Add:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Go to: https://github.com/${GITHUB_REPO}/settings/secrets/actions"
echo ""
echo "Add these repository secrets:"
echo ""
echo "1. GCP_PROJECT_ID"
echo "   Value: $PROJECT_ID"
echo ""
echo "2. WIF_PROVIDER"
echo "   Value: $WIF_PROVIDER"
echo ""
echo "3. WIF_SERVICE_ACCOUNT"
echo "   Value: $SA_EMAIL"
echo ""
echo "4. GKE_CLUSTER_NAME"
echo "   Value: $CLUSTER_NAME"
echo ""
echo "5. GKE_CLUSTER_ZONE"
echo "   Value: $CLUSTER_ZONE"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📝 Next Steps:"
echo "1. Add the above secrets to your GitHub repository"
echo "2. Commit and push your updated workflow files"
echo "3. The GitHub Action will automatically deploy to GKE"
echo ""
echo "To add secrets via command line (requires GitHub CLI):"
echo "gh secret set GCP_PROJECT_ID -b\"$PROJECT_ID\""
echo "gh secret set WIF_PROVIDER -b\"$WIF_PROVIDER\""
echo "gh secret set WIF_SERVICE_ACCOUNT -b\"$SA_EMAIL\""
echo "gh secret set GKE_CLUSTER_NAME -b\"$CLUSTER_NAME\""
echo "gh secret set GKE_CLUSTER_ZONE -b\"$CLUSTER_ZONE\""
echo ""
echo "✅ All configuration is complete!"
echo ""

# Save configuration to file
cat > wif-config.txt << EOF
AgentKit WIF Configuration
Generated: $(date)

GCP_PROJECT_ID=$PROJECT_ID
PROJECT_NUMBER=$PROJECT_NUMBER
WIF_PROVIDER=$WIF_PROVIDER
WIF_SERVICE_ACCOUNT=$SA_EMAIL
GKE_CLUSTER_NAME=$CLUSTER_NAME
GKE_CLUSTER_ZONE=$CLUSTER_ZONE
GITHUB_REPO=$GITHUB_REPO
EOF

echo "💾 Configuration saved to: wif-config.txt"
echo ""
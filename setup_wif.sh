#!/usr/bin/env bash
set -euo pipefail

GITHUB_USER="your-github-user"
REPO_NAME="your-repo-name"
PROJECT_ID="your-gcp-project-id"
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" \
                 --format='value(projectNumber)')
POOL_ID="github"
PROVIDER_ID="github-provider"
REGION="global"
REPO="${GITHUB_USER}/${REPO_NAME}"
SA_EMAIL="<YOUR_SA_EMAIL>"  # e.g. "github-composer-deployer@${PROJECT_ID}.iam.gserviceaccount.com"

# 1. Create Pool (ignore errors if already exists)
gcloud iam workload-identity-pools create "$POOL_ID" \
  --project="$PROJECT_ID" --location="$REGION" \
  --display-name="GitHub Actions Pool" || true

# 2. Create OIDC Provider (ignore errors if already exists)
gcloud iam workload-identity-pools providers create-oidc "$PROVIDER_ID" \
  --project="$PROJECT_ID" --location="$REGION" \
  --workload-identity-pool="$POOL_ID" \
  --display-name="GitHub OIDC Provider" \
  --issuer-uri="https://token.actions.githubusercontent.com" \
  --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository" \
  --attribute-condition="assertion.repository == '${REPO}'" || true

# 3. Bind the SA to the pool (grant it the Workload Identity User role)
gcloud iam service-accounts add-iam-policy-binding "$SA_EMAIL" \
  --project="$PROJECT_ID" \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL_ID}/attribute.repository/${REPO}"

echo -e "\n✅  Workload Identity configured:"
echo "   provider : projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL_ID}/providers/${PROVIDER_ID}"
echo "   service  : ${SA_EMAIL}"

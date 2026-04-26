#!/bin/bash
# =============================================================================
# ITGC Evidence Analyser — Azure Cloud Shell Deployment
# Run this inside Azure Cloud Shell (portal.azure.com >_ icon).
# No local Docker or CLI installs needed. ACR builds from GitHub.
# =============================================================================
set -e

# ---- CONFIGURATION ----
RESOURCE_GROUP="rg-itgc-analyser-prod"
LOCATION="uksouth"
ACR_NAME="itgcanalyseracr"
CONTAINER_APP_NAME="itgc-analyser"
STORAGE_ACCOUNT="itgcstorage"
FILE_SHARE="itgc-data"
ENVIRONMENT="itgc-analyser-env"
GITHUB_REPO="https://github.com/sethodoiasare/grc-portfolio.git"

# Check secrets
if [ -z "$ANTHROPIC_API_KEY" ]; then
  echo "ERROR: ANTHROPIC_API_KEY not set. Run: export ANTHROPIC_API_KEY=sk-ant-..."
  exit 1
fi
if [ -z "$JWT_SECRET_KEY" ]; then
  echo "ERROR: JWT_SECRET_KEY not set. Run: export JWT_SECRET_KEY=\$(openssl rand -hex 32)"
  exit 1
fi

echo "============================================"
echo " ITGC Evidence Analyser — Azure Deployment"
echo "============================================"

# ---- 1. Resource Group ----
echo "[1/7] Creating resource group: $RESOURCE_GROUP"
az group create --name "$RESOURCE_GROUP" --location "$LOCATION"

# ---- 2. Container Registry ----
echo "[2/7] Creating container registry: $ACR_NAME"
az acr create --resource-group "$RESOURCE_GROUP" \
  --name "$ACR_NAME" --sku Basic --admin-enabled true

# ---- 3. Build from GitHub and push to ACR ----
echo "[3/7] Building Docker image from GitHub repo..."
az acr build --registry "$ACR_NAME" \
  --image itgc-analyser:v1.1.0 \
  "${GITHUB_REPO}#main:projects/01-itgc-evidence-analyser"

# ---- 4. Storage Account for database persistence ----
echo "[4/7] Creating storage account: $STORAGE_ACCOUNT"
az storage account create --resource-group "$RESOURCE_GROUP" \
  --name "$STORAGE_ACCOUNT" --location "$LOCATION" \
  --sku Standard_LRS --kind StorageV2

STORAGE_KEY=$(az storage account keys list --resource-group "$RESOURCE_GROUP" \
  --account-name "$STORAGE_ACCOUNT" --query "[0].value" -o tsv)

az storage share create --account-name "$STORAGE_ACCOUNT" \
  --account-key "$STORAGE_KEY" --name "$FILE_SHARE"

# ---- 5. Container Apps Environment ----
echo "[5/7] Creating Container Apps environment..."
az containerapp env create --resource-group "$RESOURCE_GROUP" \
  --name "$ENVIRONMENT" --location "$LOCATION"

# ---- 6. Deploy Container App ----
echo "[6/7] Deploying container app..."
ACR_PASSWORD=$(az acr credential show --name "$ACR_NAME" \
  --query "passwords[0].value" -o tsv)

az containerapp create \
  --resource-group "$RESOURCE_GROUP" \
  --name "$CONTAINER_APP_NAME" \
  --environment "$ENVIRONMENT" \
  --image "${ACR_NAME}.azurecr.io/itgc-analyser:v1.1.0" \
  --registry-server "${ACR_NAME}.azurecr.io" \
  --registry-username "$ACR_NAME" \
  --registry-password "$ACR_PASSWORD" \
  --target-port 80 \
  --ingress external \
  --cpu 0.5 --memory 1.0Gi \
  --min-replicas 1 --max-replicas 3 \
  --env-vars "ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}" \
             "JWT_SECRET_KEY=${JWT_SECRET_KEY}" \
             "DATABASE_PATH=/app/data/itgc.db" \
             "EVIDENCE_STORE=/app/data/evidence"

# ---- 7. Mount Persistent Volume ----
echo "[7/7] Mounting persistent storage..."

# Register the file share as a storage mount in the environment
az containerapp env storage set \
  --resource-group "$RESOURCE_GROUP" \
  --name "$ENVIRONMENT" \
  --storage-name "itgc-data" \
  --azure-file-account-name "$STORAGE_ACCOUNT" \
  --azure-file-account-key "$STORAGE_KEY" \
  --azure-file-share-name "$FILE_SHARE" \
  --access-mode ReadWrite

# Update the container app to mount the volume
az containerapp update \
  --resource-group "$RESOURCE_GROUP" \
  --name "$CONTAINER_APP_NAME" \
  --yaml - <<YAML
properties:
  template:
    containers:
    - name: itgc-analyser
      volumeMounts:
      - volumeName: itgc-data
        mountPath: /app/data
    volumes:
    - name: itgc-data
      storageType: AzureFile
      storageName: itgc-data
YAML

# ---- Done ----
echo ""
echo "============================================"
echo " Deployment Complete!"
echo "============================================"
FQDN=$(az containerapp show --resource-group "$RESOURCE_GROUP" \
  --name "$CONTAINER_APP_NAME" \
  --query "properties.configuration.ingress.fqdn" -o tsv)
echo "   URL: https://$FQDN"
echo ""
echo " Next: Create admin account"
echo "   az containerapp exec --resource-group $RESOURCE_GROUP \\"
echo "     --name $CONTAINER_APP_NAME --command \"/bin/bash\""
echo "   (then inside: python3 seed_admin.py admin@vodafone.com <password>)"
echo "============================================"

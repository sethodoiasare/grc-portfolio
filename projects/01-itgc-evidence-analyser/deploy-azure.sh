#!/bin/bash
# =============================================================================
# ITGC Evidence Analyser — Azure Container Apps Deployment
# Run this on your Vodafone laptop after installing Azure CLI and Docker.
# =============================================================================
set -e

# ---- CONFIGURATION (change these) ----
RESOURCE_GROUP="rg-itgc-analyser-prod"
LOCATION="uksouth"
ACR_NAME="itgcanalyseracr"
CONTAINER_APP_NAME="itgc-analyser"
STORAGE_ACCOUNT="itgcstorageacc"
FILE_SHARE="itgc-data"
ENVIRONMENT="itgc-analyser-env"

# Secrets — set these before running
# export ANTHROPIC_API_KEY="sk-ant-..."
# export JWT_SECRET_KEY="$(openssl rand -hex 32)"

echo "============================================"
echo " ITGC Evidence Analyser — Azure Deployment"
echo "============================================"
echo ""

# ---- 1. Login ----
echo "[1/8] Logging into Azure..."
az login --use-device-code

# ---- 2. Resource Group ----
echo "[2/8] Creating resource group: $RESOURCE_GROUP"
az group create --name "$RESOURCE_GROUP" --location "$LOCATION"

# ---- 3. Container Registry ----
echo "[3/8] Creating container registry: $ACR_NAME"
az acr create --resource-group "$RESOURCE_GROUP" \
  --name "$ACR_NAME" --sku Basic --admin-enabled true

# ---- 4. Build & Push Docker Image ----
echo "[4/8] Building and pushing Docker image..."
az acr build --registry "$ACR_NAME" --image itgc-analyser:v1.1.0 .

# ---- 5. Storage Account for Persistent Volume ----
echo "[5/8] Creating storage account: $STORAGE_ACCOUNT"
az storage account create --resource-group "$RESOURCE_GROUP" \
  --name "$STORAGE_ACCOUNT" --location "$LOCATION" \
  --sku Standard_LRS --kind StorageV2

STORAGE_KEY=$(az storage account keys list --resource-group "$RESOURCE_GROUP" \
  --account-name "$STORAGE_ACCOUNT" --query "[0].value" -o tsv)

az storage share create --account-name "$STORAGE_ACCOUNT" \
  --account-key "$STORAGE_KEY" --name "$FILE_SHARE"

# ---- 6. Container Apps Environment ----
echo "[6/8] Creating Container Apps environment..."
az containerapp env create --resource-group "$RESOURCE_GROUP" \
  --name "$ENVIRONMENT" --location "$LOCATION"

# ---- 7. Deploy Container App ----
echo "[7/8] Deploying container app..."
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
             "EVIDENCE_STORE=/app/data/evidence" \
  --secrets "anthropic-key=${ANTHROPIC_API_KEY}" "jwt-secret=${JWT_SECRET_KEY}" \
  --secret-env-vars "ANTHROPIC_API_KEY=anthropic-key" "JWT_SECRET_KEY=jwt-secret"

# ---- 8. Mount Persistent Volume ----
echo "[8/8] Mounting persistent storage..."
az containerapp env storage set \
  --resource-group "$RESOURCE_GROUP" \
  --name "$ENVIRONMENT" \
  --storage-name "itgc-data" \
  --azure-file-account-name "$STORAGE_ACCOUNT" \
  --azure-file-account-key "$STORAGE_KEY" \
  --azure-file-share-name "$FILE_SHARE" \
  --access-mode ReadWrite

# Update container app with volume mount
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
  --name "$CONTAINER_APP_NAME" --query "properties.configuration.ingress.fqdn" -o tsv)
echo "URL: https://$FQDN"
echo ""
echo "Next: Seed your admin account:"
echo "  python3 seed_admin.py admin@vodafone.com <your-password>"
echo "============================================"

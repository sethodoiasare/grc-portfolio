# Azure Deployment Guide — ITGC Evidence Analyser

## What You Need on Your Vodafone Laptop

1. **Azure CLI** — `winget install Microsoft.AzureCLI` or download from portal.azure.com
2. **Docker Desktop** — installed and running
3. **This project** — cloned from `github.com/sethodoiasare/grc-portfolio`

## Before You Start

Set your secrets as environment variables:

```bash
export ANTHROPIC_API_KEY="sk-ant-api03-your-key-here"
export JWT_SECRET_KEY="$(openssl rand -hex 32)"
```

Save the JWT secret — you'll need it for future deployments.

## Deployment (Single Command)

```bash
cd projects/01-itgc-evidence-analyser
chmod +x deploy-azure.sh
./deploy-azure.sh
```

## What the Script Does

| Step | Action |
|------|--------|
| 1 | Logs into Azure (opens browser for device code) |
| 2 | Creates resource group `rg-itgc-analyser-prod` in UK South |
| 3 | Creates Azure Container Registry `itgcanalyseracr` |
| 4 | Builds Docker image and pushes to ACR |
| 5 | Creates storage account + file share for persistent SQLite DB |
| 6 | Creates Container Apps environment |
| 7 | Deploys container app (0.5 CPU, 1GB RAM, auto-scales to 3 replicas) |
| 8 | Mounts persistent volume at `/app/data` |

## After Deployment

### Seed the admin account

SSH into the container:
```bash
az containerapp exec --resource-group rg-itgc-analyser-prod \
  --name itgc-analyser --command "/bin/bash"
```

Then inside the container:
```bash
python3 seed_admin.py admin@vodafone.com YourAdminPassword123!
exit
```

### Open the app

The script prints the URL at the end. It will be something like:
`https://itgc-analyser.agreeableground-uksouth.azurecontainerapps.io`

### Have auditors register

Send them the URL. They go to `/register`, create accounts with email + password, and start assessing.

## Monthly Cost Estimate

| Resource | Tier | ~Cost/mo |
|----------|------|---------|
| Container App | 0.5 CPU, 1GB, 1 replica | ~$15 |
| Container Registry | Basic | ~$5 |
| Storage Account | 1GB file share | ~$1 |
| **Total** | | **~$21/mo** |

Plus Claude API usage — ~$0.02 per assessment (with prompt caching).

## Updating the App

When you want to add features:

```bash
# 1. Pull latest code
git pull

# 2. Build and push new image
az acr build --registry itgcanalyseracr --image itgc-analyser:v1.2.0 .

# 3. Update the container app
az containerapp update --resource-group rg-itgc-analyser-prod \
  --name itgc-analyser \
  --image itgcanalyseracr.azurecr.io/itgc-analyser:v1.2.0
```

Data persists across updates — the SQLite database lives on the Azure file share.

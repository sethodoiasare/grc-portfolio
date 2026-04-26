# Azure Deployment Guide — ITGC Evidence Analyser

## Overview

Deploy using **Azure Cloud Shell** inside portal.azure.com. No local installs needed — Cloud Shell has Azure CLI, git, and everything pre-installed. The Docker image is built in Azure Container Registry directly from the GitHub repo.

---

## Step 1 — Open Cloud Shell

1. Go to **portal.azure.com** and sign in
2. Click the **Cloud Shell** icon in the top bar (looks like `>_` )
3. Select **Bash** when prompted
4. Wait for the shell to initialize (first time takes ~30 seconds)

---

## Step 2 — Run the Deployment

Paste these lines into Cloud Shell one at a time:

```bash
# Clone the repo
git clone https://github.com/sethodoiasare/grc-portfolio.git
cd grc-portfolio/projects/01-itgc-evidence-analyser

# Set your secrets
export ANTHROPIC_API_KEY="sk-ant-api03-your-key-here"
export JWT_SECRET_KEY="$(openssl rand -hex 32)"
echo "Save this JWT secret: $JWT_SECRET_KEY"

# Run deployment
chmod +x deploy-azure-cloud.sh
./deploy-azure-cloud.sh
```

When it finishes, it prints your app URL. Copy it.

---

## Step 3 — Create the Admin Account

Still in Cloud Shell:

```bash
# Find your container app name
CONTAINER="itgc-analyser"
RG="rg-itgc-analyser-prod"

# Exec into the container
az containerapp exec --resource-group $RG --name $CONTAINER --command "/bin/bash"
```

Inside the container, type:
```bash
python3 seed_admin.py admin@vodafone.com YourAdminPassword
exit
```

---

## Step 4 — Open the App

Go to the URL printed in Step 2. You'll see the login page. Sign in with the admin credentials.

Then have your audit colleagues go to `/register` to create their own accounts.

---

## What Gets Created

| Resource | Name | Purpose |
|----------|------|---------|
| Resource Group | `rg-itgc-analyser-prod` | Everything lives here |
| Container Registry | `itgcanalyseracr` | Stores Docker images |
| Container App | `itgc-analyser` | Runs the app, port 80 |
| Storage Account | `itgcstorage` | Persistent SQLite DB |
| File Share | `itgc-data` | Mounted at `/app/data` |

---

## Updating the App (When You Add Features)

I push new code to GitHub. Then you open Cloud Shell and run:

```bash
az acr build --registry itgcanalyseracr \
  --image itgc-analyser:v1.2.0 \
  https://github.com/sethodoiasare/grc-portfolio.git#main:projects/01-itgc-evidence-analyser

az containerapp update --resource-group rg-itgc-analyser-prod \
  --name itgc-analyser \
  --image itgcanalyseracr.azurecr.io/itgc-analyser:v1.2.0
```

Zero downtime. Data persists on the file share.

---

## Monthly Cost ~$21

| Resource | Cost/mo |
|----------|---------|
| Container App (0.5 CPU, 1GB) | ~$15 |
| Container Registry (Basic) | ~$5 |
| Storage (1GB file share) | ~$1 |
| **Total** | **~$21** |

Plus Claude API — ~$0.02 per assessment.

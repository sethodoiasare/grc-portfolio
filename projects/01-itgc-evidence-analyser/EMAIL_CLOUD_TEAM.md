Subject: Request — Deploy ITGC Evidence Analyser container app (small workload, ~$21/mo)

Hi [Cloud Team Contact],

I need a small container app deployed to the Microsoft Azure Enterprise subscription. It's an internal audit automation tool I've built for the Cyber Assurance team.

**What it is**: A web app that uses AI to assess audit evidence against Vodafone ITGC controls. 58 controls, 32 markets, multi-user with login.

**What I need**: Contributor access to create these resources, or for someone on your team to run the deployment script.

**Resources required (all in one resource group)**:
- 1 Container App (0.5 CPU, 1GB RAM, port 80)
- 1 Container Registry (Basic tier)
- 1 Storage Account with file share (for database persistence)
- Total cost: ~$21/month + Claude API usage (~$0.02 per assessment)

**What you need to run**:
```
git clone https://github.com/sethodoiasare/grc-portfolio.git
cd grc-portfolio/projects/01-itgc-evidence-analyser
export ANTHROPIC_API_KEY="<I will provide this securely>"
export JWT_SECRET_KEY="$(openssl rand -hex 32)"
chmod +x deploy-azure-cloud.sh
./deploy-azure-cloud.sh
```

The script is at: https://github.com/sethodoiasare/grc-portfolio/blob/main/projects/01-itgc-evidence-analyser/deploy-azure-cloud.sh

The code is open-source (MIT license), containerized with Docker, and includes a full test suite (52 tests). No outbound connections except to the Anthropic API (docs.anthropic.com).

Happy to walk through the architecture on a call.

Thanks,
Seth Odoi Asare — Cyber Assurance Manager

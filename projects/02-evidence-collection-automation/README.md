# Evidence Collection Automation

Automated audit evidence collection for Vodafone IT General Controls assurance. Collects evidence from 7 enterprise systems, normalises it into structured format, and bundles it into audit-ready packages that feed directly into the ITGC Evidence Analyser.

## Architecture

```
Evidence Collectors                  Normalisation Engine      API + Frontend
+----------------------------+     +--------------------+     +--------------------+
| Active Directory       SIM/LIVE |--> Structured JSON    |--> Collection Dashboard |
| MDM/Intune             SIM/LIVE |   Evidence Bundles   |   - Status overview    |
| Firewall Config        SIM/LIVE |   Metadata Tagging   |   - Trigger collection |
| Vuln Scanner           SIM/LIVE |   Control Mapping    |   - Evidence freshness |
| SIEM Log Extract       SIM/LIVE |   Export (JSON)      |   - Bundle & Assess    |
| Endpoint DLP           SIM/LIVE |                      |                        |
| Manual Upload          ALWAYS LIVE |                  |                        |
+----------------------------+     +--------------------+     +--------------------+
                                           |
                                           v
                                    +--------------------+
                                    | ITGC Evidence       |
                                    | Analyser (Project 1)|
                                    +--------------------+
```

## Integration Points — Real Vodafone System Mapping

Each connector runs in one of two modes: **simulated** (demo) or **live** (production). The connector's `mode` field in the database controls the dispatch. Live integration logic lives in `src/integration.py`.

| Connector | Simulated Mode | Live Integration | Real Vodafone Data Source | API / Protocol |
|-----------|---------------|-----------------|--------------------------|----------------|
| **Active Directory** | Generates 25-60 fake users | `collect_ad()` | On-prem AD or Azure AD/Entra ID | LDAP, Microsoft Graph API |
| **MDM / Intune** | Generates 40-80 fake devices | `collect_mdm()` | Vodafone Intune tenant or Workspace ONE | Microsoft Graph API, Workspace ONE REST |
| **Firewall Config** | Generates 30-80 fake rules | `collect_firewall()` | Palo Alto Panorama, Check Point MGMT, FortiManager | REST API, SSH + CLI parsing |
| **Vulnerability Scanner** | Generates 15-40 fake CVEs | `collect_vuln_scanner()` | Tenable.io, Qualys, Rapid7 | REST API |
| **SIEM Log Extractor** | Generates 20-60 fake alerts | `collect_siem()` | Microsoft Sentinel, Splunk, QRadar | KQL, REST API |
| **Endpoint DLP** | Generates 15-40 fake events | `collect_dlp()` | Microsoft Purview, Symantec DLP | Graph API, REST API |
| **Manual Upload** | N/A — always real | `collect_manual()` | Auditor-provided files (PDF, DOCX, XLSX, CSV, images, text) | File upload |

### How Integration Works

1. **Mode toggle** — Each connector has a `mode` column in the database. `"simulated"` generates demo data; `"live"` calls real system APIs.
2. **Credentials** — Stored in the `auth_config` JSON column per connector. Each connector type has its own typed config model (e.g., `ADConfig`, `FirewallConfig`) in `src/integration.py`.
3. **Dispatch** — `ConnectorBase.run()` checks the mode and environment variable `INTEGRATION_MODE`. If both are `"live"`, it calls the real integration method. Otherwise, it falls back to `simulate()`.
4. **Normalisation** — Regardless of data source, all output goes through the same normaliser → same EvidenceItem shape → same bundle → same assessment pipeline.
5. **Network** — In production, the tool sits inside Vodafone's network (or uses a jump host/VPN) to reach on-prem AD, firewalls, and internal APIs.

### Enabling Live Mode

```bash
# 1. Set the environment variable
export INTEGRATION_MODE=live

# 2. Update connector config via API
curl -X PATCH http://localhost:8002/api/v1/connectors/1 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "live",
    "auth_config": {
      "integration_type": "azure_ad",
      "tenant_id": "vodafone.onmicrosoft.com",
      "client_id": "...",
      "client_secret": "..."
    }
  }'

# 3. Trigger collection
curl -X POST http://localhost:8002/api/v1/connectors/1/run \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"market_id": 1}'
```

### Connector Config Reference

Each connector type has its own auth config schema. See `src/integration.py` for the full dataclass definitions:

- **AD**: `ADConfig` — supports `azure_ad`, `on_prem_ad`, `ldap`
- **MDM**: `MDMConfig` — supports `intune`, `workspace_one`
- **Firewall**: `FirewallConfig` — supports `panorama`, `checkpoint_mgmt`, `fortimanager`, `ssh`
- **Vuln Scanner**: `VulnScannerConfig` — supports `tenable`, `qualys`, `rapid7`, `openvas`
- **SIEM**: `SIEMConfig` — supports `sentinel`, `splunk`, `qradar`, `elastic`
- **DLP**: `DLPConfig` — supports `purview`, `symantec`, `forcepoint`

## Quick Start

```bash
# Install
pip install -r requirements.txt
cd ui && npm install && cd ..

# Seed demo data (7 connectors, 32 markets, 18+ evidence items)
python3 seed_demo_data.py

# Start backend (port 8002)
make api

# Start frontend (port 3001)
cd ui && npm run dev

# Login at http://localhost:3001
# Email: admin@vodafone.com
# Password: GRCadmin2026!
```

## API Endpoints (port 8002)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/v1/connectors` | List connectors with mode and status |
| PATCH | `/api/v1/connectors/{id}` | Update connector mode, auth config, enabled |
| POST | `/api/v1/connectors/{id}/run` | Trigger collection (simulated or live) |
| GET | `/api/v1/collections` | Collection history |
| GET | `/api/v1/collections/{id}` | Collection detail with evidence items |
| GET | `/api/v1/evidence` | Evidence library (searchable, filterable) |
| GET | `/api/v1/evidence/stats` | Freshness stats, counts by connector |
| DELETE | `/api/v1/evidence/{id}` | Delete evidence item |
| GET | `/api/v1/bundles` | List bundles |
| POST | `/api/v1/bundles` | Create bundle from evidence items |
| GET | `/api/v1/bundles/{id}/export` | Export bundle as JSON |
| POST | `/api/v1/bundles/{id}/assess` | Build P1-compatible assessment payload |
| POST | `/api/v1/evidence/upload` | Manual file upload |

## CLI

```bash
python3 -m src.cli stats                           # Evidence statistics
python3 -m src.cli collect -c sim_ad -m "DRC"      # Run connector
python3 -m src.cli list-connectors                  # List connectors
python3 -m src.cli bundle -n "Q1 Review" -i 1,2,3   # Create bundle
python3 -m src.cli export -b 1                      # Export bundle
python3 -m src.cli assess -b 1                      # Build P1 payload
```

## Project 1 Integration

Bundles can be sent directly to the ITGC Evidence Analyser:

1. Create a bundle from collected evidence items
2. Click **Assess** on the bundle, or POST to `/api/v1/bundles/{id}/assess`
3. The payload is pre-formatted for P1's `/api/v1/assess/batch` endpoint
4. Assessment results return with PASS/PARTIAL/FAIL verdicts, gap analysis, and draft findings

## Technical Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 16, React 19, Framer Motion, Tailwind CSS |
| Backend | Python FastAPI |
| Database | SQLite (WAL mode, foreign keys) |
| Auth | JWT + bcrypt, workspace isolation |
| Integration | Microsoft Graph, LDAP, SSH, REST APIs (stubs for demo) |
| Deployment | Docker, Nginx, Supervisor |

## Demo Credentials

- **URL**: `http://localhost:3001`
- **Email**: `admin@vodafone.com`
- **Password**: `GRCadmin2026!`

All connector data is marked `[SIMULATED]` in demo mode. Switch any connector to `live` mode and provide credentials for real system integration.

# P13 Audit Readiness Dashboard — Demo Walkthrough

**Start the dashboard:**

```bash
cd projects/13-audit-readiness-dashboard
make install
make demo
# Open http://localhost:8013
```

---

## Dashboard Overview

The dashboard aggregates all 12 GRC portfolio projects into a single real-time audit readiness view. It answers three questions every audit manager needs:

1. **What is the status of every control?** — Control Coverage Matrix
2. **How fresh is our evidence?** — Project Status cards with RAG indicators
3. **What deadlines are coming?** — Upcoming deadlines timeline

---

## Section 1: Stats Row

Four summary cards at the top of the dashboard:

```
┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐
│   12                │  │   739                │  │   23 / 34           │  │   5                 │
│   Total Projects    │  │   Total Tests        │  │   Controls Covered  │  │   Deadlines         │
└─────────────────────┘  └─────────────────────┘  └─────────────────────┘  └─────────────────────┘
```

- **12 projects** across the portfolio — 3 web apps, 9 CLI tools
- **739 tests** passing — verifiable code quality
- **23 of 34 controls** fully covered, 10 partial, 1 gap
- **5 upcoming deadlines** across the next 85 days

---

## Section 2: Project Status Grid

12 cards, one per project. Each card shows:

```
┌────────────────────────────────────────────┐
│ P1  ITGC Evidence Analyser          ● GREEN │
│ ▸ WEB  │  80 tests  │  Evidence: 7 days     │
│ Controls: IAM, Audit & Assurance            │
│ Last audit: 2026-04-22                      │
└────────────────────────────────────────────┘
```

### RAG Breakdown

| RAG | Count | Projects |
|-----|-------|----------|
| GREEN | 8 | P1, P2, P3, P4, P5, P8, P10, P11 |
| AMBER | 3 | P6, P9, P12 — evidence aging (15-30 days) |
| RED | 1 | P7 — evidence 60+ days stale |

### Project Details

| ID | Project | Type | Tests | Evidence Age | RAG |
|----|---------|------|-------|-------------|-----|
| P1 | ITGC Evidence Analyser | WEB | 80 | 7 days | GREEN |
| P2 | Evidence Collection Automation | WEB | 106 | 14 days | GREEN |
| P3 | Vuln SLA Tracker | WEB | 70 | 3 days | GREEN |
| P4 | DevSecOps Evidence Collector | CLI | 79 | 21 days | GREEN |
| P5 | Cloud Posture Snapshot | CLI | 73 | 12 days | GREEN |
| P6 | Policy-as-Code Starter Kit | CLI | 55 | 30 days | AMBER |
| P7 | Security Metrics Pack | CLI | 28 | 60 days | RED |
| P8 | Data Classification Scanner | CLI | 36 | 19 days | GREEN |
| P9 | Security Control Coverage Mapper | CLI | 62 | 18 days | AMBER |
| P10 | Risk Register + Scoring Engine | CLI | 64 | 11 days | GREEN |
| P11 | Vendor Questionnaire Scorer | CLI | 32 | 15 days | GREEN |
| P12 | IR Runbook Generator | CLI | 69 | 25 days | AMBER |

---

## Section 3: Control Coverage Matrix

A 34-row x 12-column matrix mapping every Vodafone control to the projects that cover it. Cells are color-coded:

- **Green (COVERED)**: Control has strong project coverage with fresh evidence
- **Amber (PARTIAL)**: Some coverage exists but gaps remain
- **Red (GAP)**: No project currently addresses this control

### Control Categories

| Category | Controls | Covered | Partial | Gap |
|----------|----------|---------|---------|-----|
| Access Control | C01-C07 | 5 | 2 | 0 |
| Endpoint Security | C08-C10 | 2 | 1 | 0 |
| Network Security | C11-C16 | 4 | 2 | 0 |
| Data Protection | C17-C20 | 3 | 1 | 0 |
| Vulnerability Management | C21-C23 | 2 | 1 | 0 |
| SIEM & Monitoring | C24-C27 | 2 | 2 | 0 |
| Incident Response | C28-C29 | 2 | 0 | 0 |
| Supplier Security | C30-C31 | 0 | 1 | 1 |
| Risk Management | C32-C33 | 2 | 0 | 0 |
| Compliance | C34 | 1 | 0 | 0 |

### Key Finding: 1 Gap

**C31 — Supplier Service Monitoring**: Only covered by P11 (Vendor Questionnaire Scorer), which handles initial assessment but not ongoing monitoring. This maps to Vodafone Supplier Security controls (CYBER_038). Needs: a dedicated supplier continuous monitoring module or integration with a TPRM platform.

### 10 Partial Controls

Examples include:
- **C04 — Access Rights Review**: P2 + P9 cover initial review, missing periodic re-certification
- **C06 — Multi-Factor Authentication**: P6 policy check only, no enforcement verification
- **C23 — Penetration Testing**: P10 risk register tracks it but no automated test scheduling
- **C26 — Incident Event Management**: Covered by P3 (alerting) and P7 (metrics) but no SOAR integration

---

## Section 4: Upcoming Deadlines

5 deadlines displayed as a timeline:

| ID | Description | Date | Days Left | Priority |
|----|-------------|------|-----------|----------|
| DL1 | Annual IAM Control Review — Privileged Access (C03) | 2026-05-13 | 14 | HIGH |
| DL2 | Q2 Vulnerability Management Audit — Patch Compliance (C21/C22) | 2026-05-20 | 21 | HIGH |
| DL3 | Supplier Risk Re-assessment — Vendor Questionnaires (C30/C31) | 2026-06-03 | 35 | MEDIUM |
| DL4 | Cloud Security Posture Review — CIS Benchmarks (C12-C14) | 2026-06-28 | 60 | MEDIUM |
| DL5 | Data Privacy Compliance Check — PII Protection (C20) | 2026-07-23 | 85 | LOW |

---

## Section 5: Overall Assessment

The dashboard footer provides a narrative summary:

**Overall RAG: RED** — due to P7's 60-day stale evidence. This is realistic for a live portfolio where at least one tool's evidence needs a refresh.

**Recommendations:**
1. Refresh P7 (Security Metrics Pack) evidence — 60 days stale, the main drag on overall RAG
2. Address the 1 gap (C31 Supplier Service Monitoring) — needs a dedicated continuous monitoring module
3. Review 10 partial controls — each has some coverage but needs enrichment
4. Prepare for DL1 (Annual IAM Review) and DL2 (Q2 Vuln Audit) — both HIGH priority within 21 days

---

## API Reference

The dashboard is backed by a FastAPI REST API. All data is available as JSON:

| Endpoint | Description | Demo File |
|----------|-------------|-----------|
| `GET /` | Dashboard HTML page | (served as HTML) |
| `GET /api/health` | Health check | — |
| `GET /api/dashboard` | Full dashboard data | `dashboard-api-response.json` |
| `GET /api/projects` | All 12 projects | `projects-api-response.json` |
| `GET /api/projects/{id}` | Single project detail | — |
| `GET /api/controls` | All 34 controls | `controls-api-response.json` |
| `GET /api/controls/gaps` | Partial + gap controls (11) | `controls-gaps-api-response.json` |
| `GET /api/deadlines` | 5 upcoming deadlines | `deadlines-api-response.json` |
| `GET /api/stats` | Summary statistics | `stats-api-response.json` |

### Example: curl the dashboard

```bash
# Get summary stats
curl http://localhost:8013/api/stats | python3 -m json.tool

# Get gap controls
curl http://localhost:8013/api/controls/gaps | python3 -m json.tool

# Get upcoming deadlines
curl http://localhost:8013/api/deadlines | python3 -m json.tool
```

---

## Architecture

```
Browser (http://localhost:8013)
    │
    ▼
FastAPI (src/api.py)
    │
    ├── GET / → Jinja2 template (src/templates/dashboard.html)
    ├── GET /api/* → JSON endpoints (src/demo_data.py)
    │
    ▼
DemoData (src/demo_data.py)
    ├── 12 ProjectInfo objects
    ├── 34 ControlCoverage objects
    ├── 5 Deadline objects
    └── SummaryStats
```

- **No database** — demo mode uses in-memory Python objects
- **No npm/build step** — vanilla HTML/CSS served by FastAPI
- **Single command** — `make demo` starts everything
- **All API data available** as JSON for integration with other tools

---

## Production Readiness

To move from demo to production:

1. **Replace demo_data.py** with a database layer (PostgreSQL or SQLite)
2. **Add authentication** — FastAPI middleware for OAuth2/JWT
3. **Live data ingestion** — webhooks or polling to pull real project status
4. **Add alerting** — email/Slack notifications for approaching deadlines
5. **Deploy** — Docker container + reverse proxy (Nginx/Caddy)

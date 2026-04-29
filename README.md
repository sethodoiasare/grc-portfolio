# GRC Portfolio

![Python](https://img.shields.io/badge/Python-3.12+-blue)
![TypeScript](https://img.shields.io/badge/TypeScript-5.x-3178C6)
![Next.js](https://img.shields.io/badge/Next.js-16-black)
![Tests](https://img.shields.io/badge/tests-760%2B%20passing-brightgreen)
![Projects](https://img.shields.io/badge/projects-13-blue)
![Status](https://img.shields.io/badge/status-13%2F13%20complete-brightgreen)

**AI-powered GRC engineering portfolio** — 13 security automation tools spanning IT general controls, identity governance, vulnerability management, DevSecOps assurance, cloud security posture, policy-as-code, security metrics, data classification, control mapping, risk management, vendor assessment, incident response, and audit readiness.

---

## Projects

### Complete

| # | Project | Description | Tests |
|---|---------|-------------|-------|
| 1 | [ITGC Evidence Analyser](projects/01-itgc-evidence-analyser/) | AI-powered evidence assessment against Vodafone controls. Full-stack: FastAPI + Next.js + Claude API | 80+ |
| 2 | [Evidence Collection Automation](projects/02-evidence-collection-automation/) | Automated audit evidence collection across 7 enterprise systems. Connectors, normalizer, bundler | 60+ |
| 3 | [Vuln SLA Tracker](projects/03-vuln-sla-tracker/) | Scanner ingestion, SLA breach engine, Plotly dashboards for vulnerability management | 70+ |
| 4 | [DevSecOps Evidence Collector](projects/04-devsecops-evidence-collector/) | GitHub Action + Python library. SAST/SCA/secrets/DAST → D1-D8 audit evidence with HMAC signing | 79 |
| 5 | [Cloud Posture Snapshot](projects/05-cloud-posture-snapshot/) | CLI for 52 CIS benchmarks across AWS/Azure/GCP. Mock mode, branded PDF reports | 73 |
| 6 | [Policy-as-Code Starter Kit](projects/06-policy-as-code/) | 12 Rego policies (IAM, encryption, logging, networking) + Python evaluator | 55 |
| 7 | [Security Metrics Pack](projects/07-security-metrics-pack/) | MTTD/MTTR, alert quality, vuln SLA computation with matplotlib PNG charts | 28 |
| 8 | [Data Classification Scanner](projects/08-data-classification-scanner/) | Regex-based PII/PCI/PHI/secrets detection across 14 patterns with false-positive filtering | 36 |
| 9 | [IAM Access Lifecycle Simulator](projects/02-access-lifecycle-simulator/) | AD/HR/ITSM data ingestion. Leaver detection, orphaned accounts, MFA gaps, self-approval violations → access certification pack | 46 |
| 10 | [Security Control Coverage Mapper](projects/09-control-coverage-mapper/) | Parse policy docs (ISO 27001, NIST CSF, CIS v8, Vodafone). Fuzzy matching, coverage heatmaps, gap analysis | 59 |
| 11 | [Vendor Security Questionnaire Scorer](projects/11-vendor-security-questionnaire-scorer/) | Ingest vendor questionnaires (CSV/Excel). Weighted scoring across 7 categories. Risk rating + remediation checklist | 31 |
| 12 | [Risk Register + Scoring Engine](projects/10-risk-register-scoring-engine/) | Full CRUD risk register. CVSS v3.1 + SSVC v2 scoring. 5x5 risk matrix, acceptance workflows, JSON/CSV export | 63 |
| 13 | [Incident Response Runbook Generator](projects/12-incident-response-runbook-generator/) | 6 runbook templates (230+ actions). AI customization engine, markdown/JSON/PDF export | 69 |
| 14 | [Audit Readiness Dashboard](projects/13-audit-readiness-dashboard/) | Web dashboard aggregating all 12 projects: control matrix, evidence freshness, deadlines. FastAPI + vanilla HTML/CSS | 22 |

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        GRC Portfolio Ecosystem                            │
│                                                                          │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────┐  │
│  │  P1 ITGC Evidence │  │  P2 Evidence      │  │  P3 Vuln SLA         │  │
│  │  Analyser         │  │  Collection       │  │  Tracker             │  │
│  │  (Web App)        │  │  Automation       │  │  (Web App)           │  │
│  └────────┬─────────┘  └────────┬─────────┘  └──────────┬───────────┘  │
│           │                     │                        │               │
│  ┌────────┴─────────┐  ┌────────┴─────────┐  ┌──────────┴───────────┐  │
│  │  P4 DevSecOps    │  │  P5 Cloud         │  │  P6 Policy-as-Code   │  │
│  │  Evidence Coll.   │  │  Posture Snapshot │  │  Starter Kit         │  │
│  │  (GitHub Action)  │  │  (CLI)            │  │  (CLI)               │  │
│  └────────┬─────────┘  └────────┬─────────┘  └──────────┬───────────┘  │
│           │                     │                        │               │
│  ┌────────┴─────────┐  ┌────────┴─────────┐  ┌──────────┴───────────┐  │
│  │  P7 Security     │  │  P8 Data          │  │  P9 IAM Lifecycle    │  │
│  │  Metrics Pack    │  │  Classification   │  │  Simulator           │  │
│  │  (CLI)           │  │  Scanner (CLI)    │  │  (CLI)               │  │
│  └────────┬─────────┘  └────────┬─────────┘  └──────────┬───────────┘  │
│           │                     │                        │               │
│  ┌────────┴─────────┐  ┌────────┴─────────┐  ┌──────────┴───────────┐  │
│  │  P10 Risk Register│  │  P11 Vendor       │  │  P12 IR Runbook      │  │
│  │  + Scoring Engine │  │  Questionnaire    │  │  Generator           │  │
│  │  (CLI)            │  │  Scorer (CLI)     │  │  (CLI + Claude)      │  │
│  └────────┬─────────┘  └────────┬─────────┘  └──────────┬───────────┘  │
│           │                     │                        │               │
│  ┌────────┴─────────────────────┴────────────────────────┴───────────┐  │
│  │  P13 Audit Readiness Dashboard (Web App)                            │  │
│  │  Aggregates all 12 projects → RAG cards, deadlines, control matrix │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    Shared Framework                                │   │
│  │  • Vodafone Controls Mapping (30+ Tier 2/3 controls)              │   │
│  │  • D/E Statement traceability for all findings                    │   │
│  │  • Consistent RAG scoring (GREEN/AMBER/RED)                       │   │
│  │  • JSON + PDF report generation                                   │   │
│  │  • Dataclass-based domain models                                  │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Vodafone Control Coverage

Every project maps findings to the Vodafone Tier 2/3 control framework:

| Standard | Controls | Covered By |
|----------|----------|------------|
| CYBER_038 — Secure System Management | IAM, encryption, logging, networking hardening | P1, P5, P6, P9 |
| CYBER/STD/014 — Secure Agile Development | SAST, SCA, secrets, DAST, review gates | P4 |
| CYBER_062 — Secure SDLC | Pipeline security, code review, dependency mgmt | P4 |
| IAM Lifecycle | Joiner/mover/leaver, access certification | P2b, P9 |
| Vulnerability Management | SLA breach tracking, KPI dashboards | P3, P10 |
| Risk Management | Risk register, scoring, acceptance | P10 |
| Supplier Security | Vendor assessments, questionnaire scoring | P11 |
| Incident Response | Runbook generation, response planning | P12 |
| Control Assurance | Evidence assessment, control mapping, coverage | P1, P9, P13 |

---

## Quick Start

Every project is self-contained with its own `Makefile`, `requirements.txt`, and test suite.

```bash
# Clone
git clone https://github.com/sethodoiasare/grc-portfolio.git
cd grc-portfolio

# Any project
cd projects/<project-dir>
make install
make test
make demo
```

### Run all tests

```bash
for dir in projects/*/; do
  echo "=== $dir ===" && (cd "$dir" && python3 -m pytest tests/ -q) || true
done
```

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Python 3.12+, FastAPI (P1, P13), Flask (P3) |
| Frontend | Next.js 16, React 19, TypeScript (P1, P2, P13) |
| AI/ML | Claude API (P1, P12), NLP entity extraction |
| PDF Reports | ReportLab (P1, P5) |
| Charts | Plotly (P3), Matplotlib (P7, P9) |
| CI/CD | GitHub Actions (P4) |
| Policy Engine | OPA/Rego (P6) |
| Document Parsing | pdfplumber, python-docx, openpyxl (P9, P11) |
| Scoring | CVSS v3.1, SSVC (P10) |
| Testing | Pytest (all), Vitest (P1, P2, P13) |
| Data | SQLite, Dataclasses (all) |

---

## Design Principles

- **Surgical changes.** Each project touches only its own directory.
- **Mock-first.** Every project works without cloud credentials or external APIs.
- **Tested.** No project ships with fewer than 25 tests.
- **Self-documenting.** Each project has its own README with architecture, quick start, and test reference.
- **Vodafone-mapped.** Every finding traces to a D/E control statement.
- **Complete.** No half-finished features. No "TODO for later." Working code, working demos.

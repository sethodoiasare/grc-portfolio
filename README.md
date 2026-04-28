# GRC Portfolio

![Python](https://img.shields.io/badge/Python-3.12+-blue)
![TypeScript](https://img.shields.io/badge/TypeScript-5.x-3178C6)
![Next.js](https://img.shields.io/badge/Next.js-16-black)
![Tests](https://img.shields.io/badge/tests-460%2B%20passing-brightgreen)
![Projects](https://img.shields.io/badge/projects-8-blue)

**AI-powered GRC engineering portfolio** demonstrating automation across IT general controls, identity governance, vulnerability management, DevSecOps assurance, cloud security posture, policy-as-code, security metrics, and data classification.

---

## Projects

| # | Project | Description | Tests |
|---|---------|-------------|-------|
| 1 | [ITGC Evidence Analyser](projects/01-itgc-evidence-analyser/) | AI-powered evidence assessment against Vodafone controls. Full-stack: FastAPI + Next.js + Claude API | 80+ |
| 2 | [Evidence Collection Automation](projects/02-evidence-collection-automation/) | Automated audit evidence collection across systems. Config UI, connectors, evidence rendering | 60+ |
| 3 | [Vuln SLA Tracker](projects/03-vuln-sla-tracker/) | Scanner ingestion, SLA breach engine, Plotly dashboards for vulnerability management | 70+ |
| 4 | [DevSecOps Evidence Collector](projects/04-devsecops-evidence-collector/) | GitHub Action + Python library. SAST/SCA/secrets/DAST → D1-D8 audit evidence with HMAC signing | 79 |
| 5 | [Cloud Posture Snapshot](projects/05-cloud-posture-snapshot/) | CLI for CIS benchmarks across AWS/Azure/GCP. Mock mode, branded PDF reports | 73 |
| 6 | [Policy-as-Code Starter Kit](projects/06-policy-as-code/) | 12 Rego policies (IAM, encryption, logging, networking) + Python evaluator | 55 |
| 7 | [Security Metrics Pack](projects/07-security-metrics-pack/) | MTTD/MTTR, alert quality, vuln SLA with PNG chart generation | 28 |
| 8 | [Data Classification Scanner](projects/08-data-classification-scanner/) | Regex-based PII/PCI/PHI/secrets detection with false-positive filtering | 36 |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     GRC Portfolio Ecosystem                       │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │   P1 ITGC     │  │  P2 Evidence  │  │  P3 Vuln SLA         │  │
│  │   Evidence    │  │  Collection   │  │  Tracker             │  │
│  │   Analyser    │  │  Automation   │  │                      │  │
│  │  (Web App)    │  │  (Web App)    │  │  (Web App)           │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘  │
│         │                 │                      │               │
│  ┌──────┴───────┐  ┌──────┴───────┐  ┌──────────┴───────────┐  │
│  │  P4 DevSecOps │  │ P5 Cloud     │  │  P6 Policy-as-Code   │  │
│  │  Evidence     │  │ Posture      │  │  Starter Kit         │  │
│  │  Collector    │  │ Snapshot     │  │                      │  │
│  │  (GitHub Act) │  │ (CLI)        │  │  (CLI)               │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘  │
│         │                 │                      │               │
│  ┌──────┴───────┐  ┌──────┴──────────────────────┴───────────┐  │
│  │ P7 Security  │  │  P8 Data Classification Scanner          │  │
│  │ Metrics Pack │  │  (CLI)                                   │  │
│  │ (CLI)        │  │                                          │  │
│  └──────────────┘  └──────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Shared Framework                              │   │
│  │  • Vodafone Controls Mapping (30+ Tier 2/3 controls)      │   │
│  │  • D/E Statement traceability for all findings           │   │
│  │  • Consistent RAG scoring (GREEN/AMBER/RED)              │   │
│  │  • JSON + PDF report generation                          │   │
│  │  • Dataclass-based domain models                         │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Vodafone Control Coverage

Every project maps findings to the Vodafone Tier 2/3 control framework:

| Standard | Controls | Covered By |
|----------|----------|------------|
| CYBER_038 — Secure System Management | IAM, encryption, logging, networking hardening | P1, P5, P6 |
| CYBER/STD/014 — Secure Agile Development | SAST, SCA, secrets, DAST, review gates | P4 |
| CYBER_062 — Secure SDLC | Pipeline security, code review, dependency mgmt | P4 |
| IAM Lifecycle | Joiner/mover/leaver, access certification | P2 |
| Vulnerability Management | SLA breach tracking, KPI dashboards | P3 |

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
| Backend | Python 3.12+, FastAPI (P1), Flask (P3) |
| Frontend | Next.js 16, React 19, TypeScript (P1, P2) |
| AI/ML | Claude API (P1), NLP entity extraction |
| PDF Reports | ReportLab (P1, P5) |
| Charts | Plotly (P3), Matplotlib (P7) |
| CI/CD | GitHub Actions (P4) |
| Policy Engine | OPA/Rego (P6) |
| Testing | Pytest, Vitest |
| Data | SQLite, Dataclasses |

---

## Design Principles

- **Surgical changes.** Each project touches only its own directory.
- **Mock-first.** Every project works without cloud credentials.
- **Tested.** No project ships with fewer than 25 tests.
- **Self-documenting.** Each project has its own README with architecture, quick start, and test reference.
- **Vodafone-mapped.** Every finding traces to a D/E control statement.

# Security Metrics Pack

![Python](https://img.shields.io/badge/Python-3.12+-blue)
![Matplotlib](https://img.shields.io/badge/Matplotlib-3.8+-orange)
![Tests](https://img.shields.io/badge/tests-28%20passing-brightgreen)

**MTTD, MTTR, alert quality, and vulnerability SLA metrics** with PNG chart generation. Computes security KPIs from structured incident/alert/vulnerability records. Designed for monthly security operations reporting.

---

## Architecture

```
┌──────────────────────────────────────────────────────┐
│               Security Metrics Pack                    │
│                                                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │  Incidents   │  │   Alerts    │  │   Vulns     │  │
│  │  (JSON)      │  │   (JSON)    │  │   (JSON)    │  │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  │
│         │                │                │          │
│         ▼                ▼                ▼          │
│  ┌──────────────────────────────────────────────┐   │
│  │            Metrics Engine                     │   │
│  │  MTTD/MTTR  │  Alert Quality  │  Vuln SLA    │   │
│  │  - detect   │  - precision    │  - breach %  │   │
│  │  - respond  │  - FP rate      │  - MTTR vuln │   │
│  │  - resolve  │  - by source    │  - overdue   │   │
│  └──────────────────┬───────────────────────────┘   │
│                     ▼                                │
│  ┌──────────────────────────────────────────────┐   │
│  │            Reporter                           │   │
│  │  JSON report  │  PNG charts (matplotlib)     │   │
│  └──────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────┘
```

---

## Metrics Computed

### MTTD / MTTR
- **MTTD** — Mean Time to Detect (hours)
- **MTTR (Respond)** — Mean Time to Respond (hours)
- **MTTR (Resolve)** — Mean Time to Resolve (hours)
- Open incident count, severity breakdown

### Alert Quality
- True/false positive counts
- Precision percentage
- False positive rate
- Per-source breakdown

### Vulnerability SLA
- SLA compliance percentage
- Breach count by severity
- MTTR for vulnerabilities
- Overdue critical count

### Charts (matplotlib)
- SLA compliance gauge
- Alert quality pie + bar
- MTTD/MTTR bar chart
- Trend line charts (if trend data provided)

---

## Quick Start

```bash
cd projects/07-security-metrics-pack
make install
make demo          # Compute metrics from demo data
make demo-charts   # Generate JSON report + PNG charts
```

Or manually:

```bash
# Demo mode
python3 -m src.cli compute --demo --output metrics-report.json

# With charts
python3 -m src.cli compute --demo --charts --chart-dir data/charts

# Custom input
python3 -m src.cli compute \
  --incidents my-incidents.json \
  --alerts my-alerts.json \
  --vulns my-vulns.json \
  --output metrics-report.json
```

---

## Running Tests

```bash
make test
```

| Module | Tests |
|--------|-------|
| `test_metrics.py` | 14 — MTTD/MTTR, alert quality, vuln SLA computation |
| `test_models.py` | 9 — dataclasses, RAG scoring, serialization |
| `test_scanner.py` | 4 — orchestration, demo data, empty data |
| `test_reporter.py` | 1 — JSON export |

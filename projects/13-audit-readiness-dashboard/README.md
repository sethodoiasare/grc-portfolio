# Audit Readiness Dashboard (P13)

Capstone web dashboard aggregating all 12 GRC portfolio projects into a single-pane-of-glass view for audit readiness tracking.

## Architecture

- **Backend**: Python FastAPI serving JSON APIs at `/api/*`
- **Frontend**: Vanilla HTML/CSS/JS rendered via Jinja2 templates (no React, no npm, no build step)
- **Data**: Built-in demo data via `src/demo_data.py` — no external dependencies or API keys

## Quick Start

```bash
# Install dependencies
make install

# Run the dashboard (opens on port 8013)
make demo

# OR run tests
make test
```

Open [http://localhost:8013](http://localhost:8013) in your browser.

## API Reference

| Endpoint | Description |
|---|---|
| `GET /` | Dashboard HTML page |
| `GET /api/health` | Health check |
| `GET /api/dashboard` | Full DashboardData JSON |
| `GET /api/projects` | List all 12 projects |
| `GET /api/projects/{id}` | Single project detail |
| `GET /api/controls` | Control coverage matrix |
| `GET /api/controls?category=X` | Filter controls by category |
| `GET /api/controls/gaps` | Only GAP/PARTIAL controls |
| `GET /api/deadlines` | Upcoming deadlines sorted |
| `GET /api/stats` | Summary statistics |

## Dashboard Sections

- **Stats Row**: Total projects (12), total tests (~739), controls covered, upcoming deadlines
- **Project Grid**: 12 project cards with RAG status, test counts, evidence freshness, type/status badges
- **Control Coverage Matrix**: 34 controls x 12 projects with color-coded coverage indicators, filterable by category
- **Deadlines Timeline**: 5 upcoming audit deadlines with priority badges and countdowns
- **Summary Section**: Overall portfolio health assessment

## Control Categories

Access Control, Endpoint Security, Network Security, Data Protection, Vulnerability Management, SIEM & Monitoring, Incident Response, Supplier Security, Risk Management, Compliance

## Tests

```bash
make test       # Run all tests (~18 tests across 3 files)
make test-cov   # Run with coverage
```

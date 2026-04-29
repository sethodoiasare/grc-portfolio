# Risk Register + Scoring Engine

A CLI-based risk management system with dual scoring (CVSS v3.1 and SSVC v2), full CRUD operations, risk acceptance workflows, and exportable reports.

## Scoring Methodology

### CVSS v3.1 (Common Vulnerability Scoring System)

Implements the full CVSS v3.1 Base Score specification:

- **Exploitability Sub Score (ESS)**: 8.22 x AV x AC x PR x UI
- **Impact Sub Score (ISS)**: 1 - [(1-C) x (1-I) x (1-A)]
- **Impact**: 6.42 x ISS (Unchanged scope) or 7.52 x (ISS - 0.029) - 3.25 x (ISS x 0.9731 - 0.02)^13 (Changed scope)
- **Base Score**: Roundup(min(Impact + ESS, 10)) for Unchanged, or Roundup(min(1.08 x (Impact + ESS), 10)) for Changed

Severity bands: NONE (0.0), LOW (0.1-3.9), MEDIUM (4.0-6.9), HIGH (7.0-8.9), CRITICAL (9.0-10.0).

### SSVC v2 (Stakeholder-Specific Vulnerability Categorization)

Implements the CISA SSVC v2 decision tree with four inputs:

- **Exploitation**: NONE / POC / ACTIVE
- **Automatable**: YES / NO
- **Technical Impact**: PARTIAL / TOTAL
- **Mission Impact**: LOW / MEDIUM / HIGH

Produces four decisions: TRACK, TRACK_STAR, ATTEND, ACT.

### Risk Matrix

5x5 likelihood vs impact matrix using 1-5 bins from 0-100 scores:
- 1-4: LOW, 5-9: MEDIUM, 10-19: HIGH, 20-25: CRITICAL

## Quick Start

```bash
make install
make demo
make test
```

## CLI Reference

```bash
# List all risks with optional filters
python3 -m src.cli list [--status ACCEPTED] [--category INFRASTRUCTURE] [--level HIGH]

# Create a new risk
python3 -m src.cli create \
  --title "SQL Injection in Login Form" \
  --category APPLICATION \
  --cvss-vector "AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H" \
  --exploitation POC --automatable YES --tech-impact TOTAL --mission-impact HIGH \
  --impact 90 --likelihood 70 --owner "appsec-team"

# View full risk detail
python3 -m src.cli view --risk-id RSK-001

# Accept a risk
python3 -m src.cli accept --risk-id RSK-001 \
  --rationale "Business accepted due to compensating controls" \
  --accepted-by "cto" --review-days 90

# Display 5x5 risk matrix
python3 -m src.cli matrix

# Export register
python3 -m src.cli export --format json --output report.json
python3 -m src.cli export --format csv --output report.csv

# Run demo
python3 -m src.cli demo
```

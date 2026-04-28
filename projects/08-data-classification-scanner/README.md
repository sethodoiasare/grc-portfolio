# Data Classification Scanner

![Python](https://img.shields.io/badge/Python-3.12+-blue)
![Tests](https://img.shields.io/badge/tests-36%20passing-brightgreen)

**Regex-based PII, PCI, PHI, and secrets detection** for files and directories. Scans text content for 14 classification patterns with false-positive filtering. Produces structured JSON reports with severity ratings.

---

## Architecture

```
┌──────────────────────────────────────────────────────┐
│            Data Classification Scanner                 │
│                                                       │
│  ┌──────────────────────────────────────────────┐    │
│  │          Classification Rules (14)             │    │
│  │                                               │    │
│  │  PII (6)     PCI (2)     PHI (1)   SECRETS(5) │    │
│  │  - email     - PAN       - NHS #   - AWS keys │    │
│  │  - NINO      - CVV                 - API keys │    │
│  │  - SSN                              - PK hdrs │    │
│  │  - phone                            - connStr  │    │
│  │  - passport                         - generic  │    │
│  │  - IP addr                                     │    │
│  └────────────────────┬─────────────────────────┘    │
│                       │                              │
│                       ▼                              │
│  ┌──────────────────────────────────────────────┐    │
│  │            Classifier Engine                  │    │
│  │  scan_file()  │  scan_directory()            │    │
│  │  Regex matching │ False-positive filtering   │    │
│  │  Context validation │ Binary skip            │    │
│  └────────────────────┬─────────────────────────┘    │
│                       ▼                              │
│  ┌──────────────────────────────────────────────┐    │
│  │            Reporter                           │    │
│  │  JSON report with file-level detail           │    │
│  └──────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────┘
```

---

## Classification Rules

| ID | Category | Severity | Detects |
|----|----------|----------|---------|
| PII-001 | PII | MEDIUM | Email addresses |
| PII-002 | PII | HIGH | UK National Insurance numbers |
| PII-003 | PII | HIGH | US Social Security numbers |
| PII-004 | PII | MEDIUM | UK phone numbers |
| PII-005 | PII | HIGH | UK passport numbers |
| PII-006 | PII | LOW | IPv4 addresses |
| PCI-001 | PCI | CRITICAL | Credit card PANs (Visa/MC/Amex/Discover) |
| PCI-002 | PCI | CRITICAL | CVV/CVC numbers (context-validated) |
| PHI-001 | PHI | HIGH | NHS numbers (context-validated) |
| SEC-001 | SECRETS | CRITICAL | AWS access key IDs |
| SEC-002 | SECRETS | CRITICAL | High-entropy base64 (potential secrets) |
| SEC-003 | SECRETS | CRITICAL | Private key headers (PEM) |
| SEC-004 | SECRETS | CRITICAL | API keys/tokens in config |
| SEC-005 | SECRETS | CRITICAL | Database connection strings |

---

## Quick Start

```bash
cd projects/08-data-classification-scanner
make install
make demo          # Scan generated demo files
```

Or manually:

```bash
# Demo mode (generates sample files with sensitive data)
python3 -m src.cli scan --demo --output classification-report.json

# Scan a directory
python3 -m src.cli scan /path/to/code --output report.json

# Scan only specific extensions
python3 -m src.cli scan /path/to/code --extensions .py .json .yml

# List all rules
python3 -m src.cli list-rules

# List rules by category
python3 -m src.cli list-rules --category SECRETS
```

---

## Running Tests

```bash
make test
```

| Module | Tests |
|--------|-------|
| `test_classifier.py` | 16 — file/directory scanning, regex patterns, FP filtering |
| `test_models.py` | 11 — rule validation, model serialization, RAG scoring |
| `test_scanner.py` | 8 — orchestration, report generation, demo data |
| `test_reporter.py` | 1 — JSON export |

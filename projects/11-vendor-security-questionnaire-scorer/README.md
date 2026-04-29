# Vendor Security Questionnaire Scorer

CLI tool to ingest completed vendor security questionnaires (CSV/Excel), score responses against risk criteria, and output a risk rating with rationale and remediation checklist.

## Scoring Methodology

Each question is scored on two dimensions:

**Answer Score:**
- YES = 1.0
- PARTIAL = 0.5
- NO = 0.0
- NA = excluded from scoring

**Weight Multiplier:**
- HIGH = 3x
- MEDIUM = 2x
- LOW = 1x

Per-category scores are computed as `sum(answer_score * weight) / sum(weight) * 100`. The overall score is the average of all category scores. Categories with zero scored questions default to 100%.

**Risk Rating Thresholds:**
- >= 85: LOW
- >= 70: MEDIUM
- >= 50: HIGH
- < 50: CRITICAL

## Quick Start

```bash
make install
make demo
make test
```

## CLI Usage

```bash
# Score a CSV questionnaire
python3 -m src.cli score --file questionnaire.csv --format both

# Run with built-in demo data
python3 -m src.cli score --demo --output data/report.json
```

## CSV Format

Required columns: `category`, `question`, `weight`, `answer`, `notes`

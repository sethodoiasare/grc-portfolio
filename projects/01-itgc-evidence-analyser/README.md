# AI ITGC Evidence Analyser

An AI-powered command-line and REST API tool that assesses IT General Controls audit evidence against Vodafone cybersecurity control standards using Claude AI.

---

**Python 3.11+** | **FastAPI** | **Claude AI (Sonnet + Haiku)** | **Vodafone Controls (CYBER/STD/017, CYBER/STD/039, CYBER/STD/014, CYBER/STD/031, CYBER_038, CYBER_007)**

---

## Overview

IT General Controls (ITGC) audits require auditors to gather, read, and systematically evaluate large volumes of evidence — procedures, access reports, log extracts, change records, and system configurations — and then determine whether each piece of evidence satisfies the design requirements (D statements) or evidence requirements (E statements) defined in the applicable control standard. Traditionally this is a manual, time-intensive process that depends heavily on the individual auditor's knowledge of the specific control framework being tested. Inconsistency between auditors, missed gaps, and the burden of drafting structured findings are well-known friction points in every audit cycle.

This tool automates that assessment pipeline by injecting each control's formal D and E statements alongside the submitted evidence into a Claude Sonnet prompt, and then parsing the model's structured JSON response into a typed `AssessmentResult`. For every FAIL or PARTIAL verdict the model produces a fully drafted audit finding — complete with observation, criteria, risk impact, recommendation, and a proposed management action — in the exact format required by Vodafone's ITGC audit programme. The result is a repeatable, defensible, and dramatically faster evidence review process that preserves the auditor's role as the final reviewer while eliminating the low-value manual drafting work.

---

## Architecture

```
Evidence Files (.txt/.pdf/.csv/.xlsx/.docx)
        |
        v
   EvidenceAssessor
        |
  +-----+------+
  |            |
ControlParser  GRCClaudeClient
  |            |
  |     +------+--------------------+
  |     | Claude Sonnet 4.6         |
  |     | (evidence assessment)     |
  |     |                           |
  |     | Claude Haiku              |
  |     | (metadata extraction)     |
  |     +---------------------------+
  |
  v
AssessmentResult
        |
  +-----+--------------+
  |                    |
JSON Report        PDF Report
(API/CLI)       (reportlab)
        |
  +-----+--------------+
  |                    |
REST API (FastAPI)   CLI (Click)
  |
  v
Web UI (Next.js 16 + React 19)
```

`ControlParser` owns the static controls dataset and formats control definitions as clean, structured text for prompt injection. `GRCClaudeClient` is a thin Anthropic SDK wrapper that handles prompt caching, model routing, and JSON response parsing. `EvidenceAssessor` orchestrates the full pipeline: control lookup, file extraction (PDF via pdfplumber, CSV via pandas), Claude dispatch, and typed result construction. `ReportGenerator` renders results as JSON reports, Rich CLI tables, or paginated PDF documents using reportlab.

The Web UI (`ui/`) provides a production-grade Next.js 16 dashboard with Framer Motion animations, glassmorphism design, multi-file evidence upload, and an assessment history viewer. See [ui/README.md](ui/README.md) for frontend details.

---

## Controls Covered

58 Vodafone ITGC controls across 10 domains:

| Domain | Controls | Standards |
|---|---|---|
| IAM (Identity & Access) | 10 | CYBER/STD/017, CYBER/STD/039 |
| Endpoint Security | 8 | CYBER/STD/008 |
| Network Security | 7 | CYBER/STD/004 |
| HR Security | 5 | CYBER/STD/017 |
| Asset Management | 5 | CYBER/STD/011 |
| Change Management | 5 | CYBER/STD/014 |
| Vulnerability Management | 6 | CYBER_007 |
| Backup & Recovery | 5 | CYBER_038 |
| Incident Management | 4 | CYBER/STD/031 |
| Physical Security | 3 | CYBER/STD/001 |

Use `python -m src.cli list-controls` to browse the full catalogue, or `python -m src.cli list-controls --domain IAM` to filter by domain.

---

## Quick Start

### Backend

```bash
# Install dependencies
pip install -r requirements.txt

# Run demo (single control assessment)
make demo

# Run batch assessment
make demo-batch

# Start API server
make api
```

### Frontend

```bash
cd ui
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) for the dashboard. Requires the backend API running on port 8001.

The demo targets `IAM_001` using the bundled sample evidence at `data/samples/sample_evidence_iam001.txt`, writes a JSON report to `/tmp/itgc_demo.json`, generates a PDF alongside it, and then prints a Rich summary table to stdout.

---

## CLI Usage

The CLI is exposed via `python -m src.cli` and provides four commands.

### assess — single control

```bash
python -m src.cli assess \
  --control IAM_001 \
  --evidence data/samples/sample_evidence_iam001.txt \
  --statement-type D \
  --output /tmp/iam001_result.json \
  --pdf
```

| Flag | Description |
|---|---|
| `--control` | Vodafone control ID (e.g. `IAM_001`) |
| `--evidence` | Path to evidence file (.txt, .pdf, .csv) |
| `--statement-type` | `D` for design requirements, `E` for evidence requirements |
| `--output` | Path to write the JSON result (optional) |
| `--pdf` | Also generate a PDF report alongside the JSON output |

### batch — multiple controls from config

```bash
python -m src.cli batch \
  --config data/samples/batch_config.yaml \
  --output-dir /tmp/itgc_batch_reports \
  --format both
```

The YAML config lists each `control_id`, `evidence_file`, and optionally `statement_type`. `--format` accepts `json`, `pdf`, or `both`.

### list-controls — browse the controls dataset

```bash
python -m src.cli list-controls
python -m src.cli list-controls --domain IAM
python -m src.cli list-controls --search "privileged"
```

Prints a formatted table of all controls with their IDs, names, standards, and statement counts. Supports optional `--domain` and `--search` filters.

### summary — print a result file

```bash
python -m src.cli summary /tmp/itgc_demo.json
python -m src.cli summary /tmp/itgc_batch_reports/assessment_report.json
```

Renders a colour-coded Rich summary table from a previously saved JSON report — useful for reviewing results without re-running an assessment.

---

## API Usage

Start the server:

```bash
make api
# or: uvicorn src.api:app --reload --port 8001
```

Interactive Swagger docs are available at `http://localhost:8001/docs`.

### Health check

```bash
curl http://localhost:8001/api/v1/health
```

```json
{"status": "ok", "version": "1.0.0", "controls_loaded": 58}
```

### List controls

```bash
curl http://localhost:8001/api/v1/controls
curl "http://localhost:8001/api/v1/controls?domain=IAM"
curl "http://localhost:8001/api/v1/controls/search?q=privileged"
curl http://localhost:8001/api/v1/controls/IAM_001
```

### Assess evidence (text body)

```bash
curl -X POST http://localhost:8001/api/v1/assess \
  -H "Content-Type: application/json" \
  -d '{
    "control_id": "IAM_001",
    "evidence_text": "User access review procedure v2.3 approved 2025-11-01 by Information Asset Owner. All leavers processed within 1 business day per HR extract attached.",
    "statement_type": "D"
  }'
```

### Assess evidence (file upload)

```bash
curl -X POST "http://localhost:8001/api/v1/assess/upload?control_id=IAM_001&statement_type=D" \
  -F "file=@data/samples/sample_evidence_iam001.txt"
```

### Batch assessment (JSON report)

```bash
curl -X POST http://localhost:8001/api/v1/assess/batch \
  -H "Content-Type: application/json" \
  -d '{
    "audit_scope": "Vodafone UK ITGC Q1 2026",
    "assessments": [
      {"control_id": "IAM_001", "evidence_text": "...", "statement_type": "D"},
      {"control_id": "VUL_001", "evidence_text": "...", "statement_type": "D"}
    ]
  }'
```

### Batch assessment (PDF download)

```bash
curl -X POST http://localhost:8001/api/v1/assess/batch/pdf \
  -H "Content-Type: application/json" \
  -d '{
    "audit_scope": "Vodafone UK ITGC Q1 2026",
    "assessments": [
      {"control_id": "IAM_001", "evidence_text": "..."},
      {"control_id": "CHG_001", "evidence_text": "..."}
    ]
  }' \
  --output itgc_report.pdf
```

---

## How Claude AI is Used

### Model selection strategy

Two models are used for different tasks based on accuracy and cost requirements:

- **Claude Sonnet 4.6** handles all evidence assessments. It receives the full control definition and the submitted evidence, and returns the structured JSON verdict. Sonnet's reasoning capability is necessary here because the model must cross-reference multiple D or E statements, identify specific gaps, assign a risk rating, and draft a structured audit finding — all in a single pass.

- **Claude Haiku** handles lightweight metadata extraction from the evidence text (evidence type, date range, systems mentioned, document count, one-sentence summary). This is a cheap pre-processing step that does not require Sonnet's reasoning depth, so routing it to Haiku keeps token costs minimal.

### Prompt caching

Both the system prompt and the static control-context block are marked with `cache_control: ephemeral`. This means that when multiple assessments are run against the same control in the same session — for example during a batch run assessing the same IAM_001 control with different evidence samples — the input-token billing for the cached prefix is reduced by approximately 90%. The cache is invalidated automatically after five minutes of inactivity.

### Assessment JSON schema

The model is instructed via the system prompt to return only a raw JSON object (no markdown fences) conforming to this schema:

```json
{
  "verdict": "PASS|PARTIAL|FAIL|INSUFFICIENT_EVIDENCE",
  "confidence": 0.0,
  "satisfied_requirements": ["D1: brief reason"],
  "gaps": ["D2: specific gap description"],
  "risk_rating": "CRITICAL|HIGH|MEDIUM|LOW|INFORMATIONAL",
  "draft_finding": {
    "title": "Finding title",
    "observation": "What was observed",
    "criteria": "Which D/E statement is not met",
    "risk_impact": "Business risk if unresolved",
    "recommendation": "Specific remediation steps",
    "management_action": "Proposed owner response and target date"
  },
  "recommended_evidence": ["Additional evidence to request"],
  "remediation_notes": "Narrative guidance for the control owner"
}
```

`draft_finding` must be `null` for PASS and INSUFFICIENT_EVIDENCE verdicts. The `_build_result` method in `EvidenceAssessor` enforces this constraint regardless of model output to guard against hallucination.

### Token cost optimisation

- Prompt caching reduces repeated control-context billing by ~90% within a session.
- Haiku handles all metadata extraction (300 max tokens vs 1,500 for Sonnet).
- CSV evidence is summarised to a maximum of 50 rows before dispatch.
- PDF pages with no extractable text are silently dropped.
- The system prompt instructs the model to return raw JSON without explanation, minimising output tokens.

---

## Output Formats

### JSON report structure

Single-assessment responses follow `AssessmentResult.to_dict()`:

```json
{
  "control_id": "IAM_001",
  "control_name": "User Registration and De-registration",
  "statement_type": "D",
  "verdict": "PARTIAL",
  "confidence": 0.82,
  "satisfied_requirements": ["D1: procedure exists", "D2: approvals evidenced"],
  "gaps": ["D4: leaver deactivation SLA exceeded in 3 samples"],
  "risk_rating": "MEDIUM",
  "draft_finding": {
    "title": "Leaver deactivation SLA not consistently met",
    "observation": "...",
    "criteria": "D4 requires deactivation within one business day",
    "risk_impact": "Former employees retain access beyond authorised period",
    "recommendation": "Automate HR-to-AD deactivation trigger",
    "management_action": "Automation scoped for Q3 2026"
  },
  "recommended_evidence": ["HR leaver report with timestamps", "AD deactivation logs"],
  "remediation_notes": "Automate the Workday-to-Active Directory deactivation trigger.",
  "assessed_at": "2026-01-15T10:00:00",
  "tokens_used": 1847,
  "model_used": "claude-sonnet-4-6"
}
```

Batch reports produced by `ReportGenerator.generate_json_report()` wrap individual results in an envelope that includes an executive summary with pass/fail/partial counts, overall RAG status, total token usage, and the audit scope metadata.

### PDF report sections

PDF reports generated by `ReportGenerator.generate_pdf_report()` contain the following sections in order:

1. Cover page with report title, audit scope, generation timestamp, and overall RAG status
2. Executive summary table: total controls assessed, pass / partial / fail / insufficient counts, overall risk rating
3. Results summary table: one row per control with control ID, name, verdict (colour-coded), confidence, and gap count
4. Detailed findings: one page per FAIL or PARTIAL result containing the full `DraftFinding` narrative
5. Recommended evidence appendix: consolidated list of additional evidence items requested across all assessed controls

---

## Running Tests

```bash
make test
```

This runs the full test suite under `tests/` using pytest with short tracebacks:

```bash
pytest tests/ -v --tb=short
```

To run with coverage reporting:

```bash
make test-cov
# or: pytest tests/ -v --tb=short --cov=src --cov-report=term-missing
```

Test modules:

| File | Scope |
|---|---|
| `tests/test_models.py` | Enum values, dataclass construction, `to_dict()`, `to_json()`, properties |
| `tests/test_control_parser.py` | Lookup, domain filtering, search, prompt formatting, data integrity |
| `tests/test_assessor_unit.py` | Assessment pipeline with mocked Claude client, batch ordering, file ingestion |
| `tests/test_api.py` | FastAPI route contracts with mocked assessor, status codes, response shapes |

All Claude API calls are mocked in the unit and API test suites so no API key or network access is required to run the test suite.

---

## Portfolio Note

This project demonstrates senior-level GRC automation thinking: integrating Claude AI into an IT audit workflow, mapping findings to named Vodafone cybersecurity controls (CYBER/STD/017, CYBER_007), producing audit-grade evidence packages, and delivering a portfolio-ready tool that reflects real Vodafone ITGC audit practice.

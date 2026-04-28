# DevSecOps Audit Evidence Collector

![Python](https://img.shields.io/badge/Python-3.12+-blue)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-composite-2088FF)
![Tests](https://img.shields.io/badge/tests-57%2B%20passing-brightgreen)

**GitHub Action + Python library** that runs SAST, SCA, secrets scanning, and DAST in CI/CD, then maps results to Vodafone DevSecOps D1-D8 control statements and produces signed audit evidence packages.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    CI/CD Pipeline                        │
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐ │
│  │ Semgrep  │  │ pip-audit│  │ Gitleaks │  │OWASP ZAP│ │
│  │  (SAST)  │  │  (SCA)   │  │ (Secrets)│  │ (DAST)  │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └───┬────┘ │
│       │              │              │            │       │
│       ▼              ▼              ▼            ▼       │
│  ┌──────────────────────────────────────────────────┐   │
│  │         Python Evidence Packager                  │   │
│  │  ┌──────────┐ ┌───────────────┐ ┌─────────────┐  │   │
│  │  │ Parsers  │ │Control Mapper │ │   Signer    │  │   │
│  │  │ Normalise │ │  D1-D8 →      │ │ HMAC-SHA256 │  │   │
│  │  │ findings │ │  Verdicts     │ │  integrity  │  │   │
│  │  └──────────┘ └───────────────┘ └─────────────┘  │   │
│  └──────────────────────┬───────────────────────────┘   │
│                         ▼                                │
│            ┌────────────────────────┐                    │
│            │  Audit Evidence JSON   │                    │
│            │  (signed, structured)  │                    │
│            └────────────────────────┘                    │
└─────────────────────────────────────────────────────────┘
```

---

## Vodafone Control Mapping (D1-D8)

| Control | Requirement | Tool Source |
|---------|-------------|-------------|
| **D1** | SAST integrated in CI pipeline | Semgrep |
| **D2** | SCA/dependency scanning in pipeline | pip-audit |
| **D3** | Secrets/credential scanning in pipeline | Gitleaks |
| **D4** | DAST performed on test/staging | OWASP ZAP |
| **D5** | Security scan results reviewed before merge | Pipeline config |
| **D6** | Critical/high findings block deployment | Pipeline gate |
| **D7** | Security findings tracked to closure | External (JIRA, etc.) |
| **D8** | Security training for developers | External (LMS) |

Standards referenced: CYBER/STD/014 (Secure Agile Development), CYBER_062 (Secure SDLC)

---

## Quick Start

### Local CLI

```bash
cd projects/04-devsecops-evidence-collector
make install
make demo                # builds evidence package from sample outputs
```

Or manually:

```bash
python -m src.cli \
  --semgrep data/sample_outputs/semgrep.json \
  --pip-audit data/sample_outputs/pip-audit.json \
  --gitleaks data/sample_outputs/gitleaks.json \
  --zap data/sample_outputs/zap.json \
  --pipeline-log data/sample_outputs/pipeline.log \
  --project "my-app" \
  --branch "main" \
  --sign \
  --output evidence-package.json
```

### GitHub Action

```yaml
- uses: ./projects/04-devsecops-evidence-collector
  with:
    audit_project: "GRC Platform"
    audit_period: "FY25-Q4"
    zap_target: "https://staging.example.com"
    signing_secret: ${{ secrets.DEVSECOPS_SIGNING_SECRET }}
```

The action uploads a signed `evidence-package.json` artifact with 90-day retention.

---

## Evidence Package Output

```json
{
  "evidence_package_id": "uuid",
  "generated_at": "ISO datetime",
  "project": "my-app",
  "branch": "main",
  "commit_sha": "abc123",
  "pipeline_run": "12345",
  "audit_period": "FY25-Q4",
  "control": "DevSecOps",
  "standard_references": ["CYBER/STD/014", "CYBER_062"],

  "coverage_summary": {
    "D1_SAST": "PARTIAL",
    "D2_SCA": "SATISFIED",
    "D3_SECRETS": "PARTIAL",
    "D4_DAST": "SATISFIED",
    "D5_REVIEW_GATE": "SATISFIED",
    "D6_BLOCKING_POLICY": "SATISFIED",
    "D7_FINDINGS_TRACKING": "NOT_APPLICABLE",
    "D8_DEVELOPER_TRAINING": "NOT_APPLICABLE"
  },

  "findings_summary": {
    "sast": {"critical": 2, "high": 2, "medium": 0, "low": 0},
    "sca": {"critical": 1, "high": 2, "medium": 1, "low": 0},
    "secrets": {"count": 3, "types": ["aws-access-key", "generic-api-key", "jwt-secret"]},
    "dast": {"critical": 0, "high": 1, "medium": 1, "low": 2}
  },

  "blocking_findings": [...],
  "gaps": [...],
  "audit_narrative": "A DevSecOps pipeline audit was conducted...",
  "signature": "hmac-sha256-hex-digest"
}
```

---

## CLI Reference

```
python -m src.cli [options]

  --semgrep PATH        Semgrep JSON output
  --pip-audit PATH      pip-audit JSON output
  --gitleaks PATH       Gitleaks JSON output
  --zap PATH            OWASP ZAP JSON report
  --pipeline-log PATH   CI pipeline log
  --all-from-dir DIR    Auto-detect all scan outputs from directory
  --project NAME        Project name
  --branch NAME         Git branch
  --commit SHA          Commit SHA
  --pipeline-run ID     Pipeline run identifier
  --audit-period PERIOD Audit period (e.g. FY25-Q3)
  --output PATH         Output path (default: evidence-package.json)
  --sign                HMAC-sign the package
  --verify PATH         Verify a signed package
  --json                Print package to stdout
```

---

## Running Tests

```bash
make test        # pytest -v --tb=short
make test-cov    # with coverage report
```

Test modules:

| Module | Tests | Coverage |
|--------|-------|----------|
| `test_parsers.py` | Semgrep, pip-audit, Gitleaks, ZAP, pipeline log | 22 tests |
| `test_control_mapper.py` | Coverage, findings, blocking, gaps, narrative | 17 tests |
| `test_packager.py` | Build, export, partial inputs, serialization | 11 tests |
| `test_signer.py` | Sign, verify, tamper detection, round-trip | 12 tests |
| `test_models.py` | All dataclasses, serialization | 10 tests |

---

## Technical Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.12+ |
| Packaging | Standard library `dataclasses` |
| Testing | Pytest |
| SAST | Semgrep |
| SCA | pip-audit |
| Secrets | Gitleaks |
| DAST | OWASP ZAP |
| Signing | HMAC-SHA256 |
| CI/CD | GitHub Actions (composite) |

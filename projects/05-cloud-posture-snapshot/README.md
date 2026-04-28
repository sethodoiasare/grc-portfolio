# Cloud Posture Snapshot

![Python](https://img.shields.io/badge/Python-3.12+-blue)
![AWS](https://img.shields.io/badge/AWS-CIS_v1.5-orange)
![Azure](https://img.shields.io/badge/Azure-CIS_v2.0-0078D4)
![GCP](https://img.shields.io/badge/GCP-CIS_v2.0-4285F4)
![Tests](https://img.shields.io/badge/tests-80%2B%20passing-brightgreen)

**CLI tool** that runs CIS benchmark checks against AWS, Azure, and GCP, maps findings to Vodafone CYBER_038 hardening standards, and produces structured JSON reports and professional PDF summaries.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                  Cloud Posture Snapshot CLI                   │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                   │
│  │   AWS    │  │  Azure   │  │   GCP    │                   │
│  │ Checker  │  │ Checker  │  │ Checker  │                   │
│  │ (22 chk) │  │ (16 chk) │  │ (14 chk) │                   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘                   │
│       │              │              │                         │
│       ▼              ▼              ▼                         │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                    Scanner                            │   │
│  │  Orchestrates checks → computes RAG → generates      │   │
│  │  management summary → maps to Vodafone controls      │   │
│  └──────────────────────┬───────────────────────────────┘   │
│                         ▼                                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                    Reporter                           │   │
│  │  export_json() ── structured JSON findings report    │   │
│  │  export_pdf()  ── branded A4 PDF with tables         │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

---

## CIS Benchmark Coverage

### AWS (CIS v1.5) — 22 checks

| Section | Checks | Examples |
|---------|--------|----------|
| 1 — IAM | 7 | Root MFA, access key rotation, password policy, no admin policies |
| 2 — Logging | 5 | CloudTrail multi-region, log validation, S3 bucket security, VPC flow logs |
| 3 — Monitoring | 3 | CloudWatch alarms for root usage, unauthorized API calls, MFA events |
| 5 — Networking | 3 | No SSH/RDP from 0.0.0.0/0, default SG blocking all traffic |
| 6 — Storage | 3 | S3 versioning, MFA delete, Block Public Access |
| 7 — Encryption | 1 | EBS encryption by default |

### Azure (CIS v2.0) — 16 checks

| Section | Checks | Examples |
|---------|--------|----------|
| 1 — Identity | 4 | MFA for owners/all users, guest review, Security Defaults |
| 2 — Defender | 3 | Defender for Servers, SQL, Storage |
| 3 — Storage | 2 | Secure transfer required, public blob disabled |
| 4 — Databases | 1 | SQL server auditing |
| 5 — Logging | 2 | Activity log alerts for policy and NSG changes |
| 6 — Networking | 3 | NSG rules for RDP/SSH, Network Watcher |
| 7 — Encryption | 1 | Azure Disk Encryption |

### GCP (CIS v2.0) — 14 checks

| Section | Checks | Examples |
|---------|--------|----------|
| 1 — IAM | 4 | No admin SAs, key rotation, user-managed keys, API key usage |
| 2 — Logging | 3 | Cloud Audit Logs, log sinks, export permissions |
| 3 — Networking | 4 | Firewall rules for SSH/RDP/all-ports, VPC flow logs |
| 4 — Storage | 1 | Public bucket access |
| 7 — Encryption | 2 | CMEK for Cloud Storage and Compute Engine disks |

---

## Vodafone Control Mapping

Every CIS check maps to a Vodafone control framework D-statement:

| CIS Section | Vodafone Control | D Statement |
|------------|-----------------|-------------|
| 1 | Management of privileged access rights | D1-D5 |
| 2 | Security event logging & monitoring | D1-D7 |
| 3 | Firewall rule base management / Segregation | D1-D10 |
| 4 | Management of technical vulnerabilities | D1-D6 |
| 5 | Compliance with hardening standards (CYBER_038) | D1-D3 |
| 6 | Information access restriction | D1-D6 |
| 7 | Protection of information in transit | D1-D17 |
| 8 | Network intrusion detection | D1-D10 |

---

## Quick Start

```bash
cd projects/05-cloud-posture-snapshot
make install
make demo           # AWS scan, JSON + PDF output
```

Or manually:

```bash
# Mock mode — no cloud credentials needed
python -m src.cli scan --provider aws --format both

# List available checks
python -m src.cli list-checks --provider azure

# Print summary from a saved report
python -m src.cli summary posture-report.json
```

### Live mode (with cloud credentials)

```bash
# AWS
export AWS_PROFILE=vdf-prod
python -m src.cli scan --provider aws --live --account-id 123456789012

# Azure (login first)
az login
python -m src.cli scan --provider azure --live --account-id your-sub-id

# GCP
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json
python -m src.cli scan --provider gcp --live --account-id your-project-id
```

---

## CLI Reference

```
cloud-posture scan [options]          Run CIS benchmark scan
cloud-posture list-checks [options]   List available checks
cloud-posture summary <report.json>   Print summary from saved report

scan options:
  --provider, -p    aws|azure|gcp (required)
  --account-id      Account/subscription/project ID
  --mock            Use mock mode (default)
  --live            Use live cloud SDK calls
  --output, -o      Output path (default: posture-report.json)
  --format, -f      json|pdf|both (default: json)
```

---

## Output

### JSON Report

```json
{
  "report_id": "uuid",
  "generated_at": "ISO datetime",
  "provider": "AWS",
  "account_id": "111122223333",
  "cis_benchmark_version": "CIS AWS Foundations v1.5",
  "summary": {
    "total_checks": 22,
    "passed": 9,
    "failed": 13,
    "not_applicable": 0,
    "pass_rate_pct": 40.9,
    "critical_failures": 3,
    "high_failures": 7
  },
  "findings": [
    {
      "check_id": "1.1",
      "check_title": "Avoid use of root account",
      "status": "PASS",
      "severity": "CRITICAL",
      "resource": "Root account",
      "finding": "Root account has no recent activity...",
      "remediation": "Remove root user access keys...",
      "vodafone_control": "Management of privileged access rights",
      "d_statement": "D1-D5"
    }
  ],
  "management_summary": "Cloud Posture Assessment — AWS...",
  "critical_failures": [...]
}
```

### PDF Report

A4 branded PDF with:
- Vodafone red cover styling
- Metadata table with RAG status
- Summary statistics table
- Management summary narrative
- Vodafone control coverage matrix
- Full findings table with colour-coded PASS/FAIL cells
- Critical/high-severity findings detail section with remediation guidance

---

## Running Tests

```bash
make test        # All 80+ tests
make test-cov    # With coverage report
```

| Module | Tests |
|--------|-------|
| `test_aws_checks.py` | 14 — individual AWS checks |
| `test_azure_checks.py` | 11 — individual Azure checks |
| `test_gcp_checks.py` | 11 — individual GCP checks |
| `test_scanner.py` | 10 — orchestration, summaries, mappings |
| `test_reporter.py` | 6 — JSON/PDF export and round-trip |
| `test_models.py` | 19 — dataclasses, enums, RAG logic |

---

## Technical Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.13+ |
| Models | Standard library `dataclasses` |
| CLI | `argparse` with subcommands |
| PDF | ReportLab (`SimpleDocTemplate`, `RLTable`) |
| Testing | Pytest |
| AWS SDK | boto3 (optional, mock mode default) |
| Azure SDK | azure-identity + azure-mgmt-* (optional) |
| GCP SDK | google-cloud-* (optional) |

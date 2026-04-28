# Policy-as-Code Starter Kit

![Python](https://img.shields.io/badge/Python-3.12+-blue)
![OPA](https://img.shields.io/badge/OPA-Regov0.68-4B8BBE)
![Tests](https://img.shields.io/badge/tests-55%20passing-brightgreen)

**12 Rego policies across IAM, encryption, logging, and networking** with a Python evaluation harness. Maps every policy to Vodafone CYBER_038 control statements. Runs in pure Python (no OPA binary required for demos).

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│           Policy-as-Code Starter Kit             │
│                                                  │
│  ┌──────────────┐   ┌────────────────────────┐  │
│  │  Rego Files   │   │  Python Evaluator      │  │
│  │  (12 .rego)   │   │  (evaluator.py)        │  │
│  │              │   │                        │  │
│  │  IAM (4)     │   │  Pure-Python fallback  │  │
│  │  Encryption  │   │  when OPA unavailable  │  │
│  │  (3)         │   │                        │  │
│  │  Logging (3)  │   │  Same verdicts as OPA  │  │
│  │  Networking  │   │                        │  │
│  │  (2)         │   │                        │  │
│  └──────┬───────┘   └───────────┬────────────┘  │
│         │                       │                │
│         ▼                       ▼                │
│  ┌──────────────────────────────────────────┐   │
│  │              Scanner                       │   │
│  │  Evaluates policies against JSON input    │   │
│  │  Computes RAG → maps Vodafone controls   │   │
│  └──────────────────┬───────────────────────┘   │
│                     ▼                            │
│  ┌──────────────────────────────────────────┐   │
│  │              Reporter                      │   │
│  │  JSON export with compliance breakdown    │   │
│  └──────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
```

---

## Policy Coverage

| ID | Category | Severity | Title |
|----|----------|----------|-------|
| IAM-001 | IAM | CRITICAL | Least Privilege — No Wildcard Actions |
| IAM-002 | IAM | CRITICAL | No Attached Admin Policies |
| IAM-003 | IAM | HIGH | MFA Required for Privileged Users |
| IAM-004 | IAM | HIGH | Access Key Rotation (90 days) |
| ENC-001 | Encryption | HIGH | S3 Buckets Must Use SSE |
| ENC-002 | Encryption | HIGH | EBS Volumes Must Be Encrypted |
| ENC-003 | Encryption | HIGH | RDS Instances Must Be Encrypted |
| LOG-001 | Logging | HIGH | CloudTrail Multi-Region |
| LOG-002 | Logging | MEDIUM | CloudTrail Log File Validation |
| LOG-003 | Logging | MEDIUM | VPC Flow Logs Enabled |
| NET-001 | Networking | CRITICAL | No Unrestricted SSH (0.0.0.0/0) |
| NET-002 | Networking | CRITICAL | No Unrestricted RDP (0.0.0.0/0) |

---

## Vodafone Control Mapping

| Category | Control | D Statement |
|----------|---------|-------------|
| iam | Management of privileged access rights | D1-D5 |
| encryption | Protection of information in transit and at rest | D1-D17 |
| logging | Security event logging and monitoring | D1-D7 |
| networking | Network security and segregation | D1-D10 |

---

## Quick Start

```bash
cd projects/06-policy-as-code
make install
make demo          # Run against built-in demo data
```

Or manually:

```bash
# Run with demo data
python3 -m src.cli scan --demo --output policy-report.json

# Run against custom input
python3 -m src.cli scan --input src/data/sample_input.json

# List all policies
python3 -m src.cli list-policies

# List by category
python3 -m src.cli list-policies --category iam
```

---

## Running Tests

```bash
make test
```

| Module | Tests |
|--------|-------|
| `test_evaluator.py` | 30 — individual policy evaluations |
| `test_scanner.py` | 10 — orchestration, summaries, RAG |
| `test_models.py` | 11 — models, Vodafone mappings, Rego existence |
| `test_reporter.py` | 2 — JSON export |

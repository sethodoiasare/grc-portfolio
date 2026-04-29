# IAM Access Lifecycle Simulator

CLI-based IAM audit simulator that detects access lifecycle violations from AD, HR, and ITSM data.

## What It Detects

| Violation | Description | Severity |
|---|---|---|
| LEAVER_ACTIVE | Leaver in HR but AD account still enabled | CRITICAL |
| ORPHANED | AD account with no matching HR record | HIGH |
| MFA_MISSING | No MFA on enabled account (HIGH for privileged) | HIGH / MEDIUM |
| SELF_APPROVAL | ITSM ticket approved by requester (SoD violation) | HIGH |

## Quick Start

```bash
make install
make demo
```

## CLI Commands

```bash
# Run with built-in demo data
python3 -m src.cli scan --demo --cert-report

# Run with custom data files
python3 -m src.cli scan --ad-file data/samples/ad_export.csv --hr-file data/samples/hr_export.csv --itsm-file data/samples/itsm_log.csv --output data/audit-report.json
```

## Running Tests

```bash
make test
```

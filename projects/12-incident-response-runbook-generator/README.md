# Incident Response Runbook Generator

Battle-tested incident response runbook generator with AI-assisted customisation. Covers 6 incident types across 6 IR stages -- designed for real incident responders to use as a practical checklist during live incidents.

## Incident Types

| Type | Description |
|------|-------------|
| malware | Virus/worm/trojan outbreak -- detection, containment, eradication, recovery |
| ransomware | Ransomware encryption attack -- network isolation, backup protection, decryption workflow |
| breach | Unauthorised data access/exfiltration -- DLP, regulatory notification, dark web monitoring |
| ddos | Distributed denial-of-service -- CDN scrubbing, rate limiting, ISP coordination |
| insider | Malicious or negligent insider -- UEBA, HR/Legal coordination, evidence preservation |
| credential | Compromised credentials -- session revocation, MFA enforcement, persistence hunting |

## IR Stages

Each runbook covers 6 stages: Identification, Containment, Eradication, Recovery, Post-Incident Analysis, and Lessons Learned & Closure. Stages include responsible teams, SLA targets, and escalation triggers.

## AI Customisation

Runbooks are customised to your organisation context: industry, regulatory requirements, threat profile, and technology stack. Tool names, contacts, and regulatory actions are intelligently injected.

## Quick Start

```bash
# Install
make install

# Run demo (generates 2 runbooks for a fintech org)
make demo

# List available templates
python3 -m src.cli list-templates

# Generate a single runbook
python3 -m src.cli generate --type ransomware --severity SEV2

# Generate all 6 runbooks
python3 -m src.cli generate --type all --output-dir data

# Run tests
make test
```

# Projects Showcase

13 security automation tools. 480+ tests. Built for audit reality.

---

## AI-Powered ITGC Evidence Analyser
*FastAPI · Next.js · Claude API · ReportLab | [GitHub](https://github.com/sethodoiasare/grc-portfolio/tree/main/projects/01-itgc-evidence-analyser)*

Automated assessment of IT general controls audit evidence against 30+ Vodafone D/E control statements. Upload evidence → AI evaluates against control criteria → structured verdict with findings, gaps, and remediation. Full-stack web application with conversational follow-up and branded PDF reports.

**Why it matters:** Turns weeks of manual evidence review into minutes. Every finding traceable to a control statement — auditor-ready output.

---

## Evidence Collection Automation
*FastAPI · 7 Enterprise Connectors · SQLite | [GitHub](https://github.com/sethodoiasare/grc-portfolio/tree/main/projects/02-evidence-collection-automation)*

Pluggable connectors for Active Directory, HR, ITSM, firewall, EDR, DLP, and IAM systems. Normalises heterogeneous outputs into structured evidence packages with metadata, timestamps, and integrity hashes.

**Why it matters:** Eliminates the most painful part of audit preparation — manual evidence gathering across systems.

---

## IAM Access Lifecycle Simulator
*Python · Violation Detection Engine · Access Certification | [GitHub](https://github.com/sethodoiasare/grc-portfolio)*

Ingests AD, HR, and ITSM data exports. Detects leavers with active access, orphaned accounts, privileged users without MFA, and self-approval violations. Generates access certification packs with REVOKE/REVIEW/CONFIRM actions per account.

**Why it matters:** IAM audit findings that take consultants weeks to produce — automated in seconds.

---

## Vulnerability SLA Tracker
*Plotly · Flask · SQLite | [GitHub](https://github.com/sethodoiasare/grc-portfolio/tree/main/projects/03-vuln-sla-tracker)*

Ingests Nessus, OpenVAS, and Qualys scanner exports. Applies SLA rules by CVSS severity. Tracks breach status, computes KPIs, generates interactive dashboards.

**Why it matters:** Real-time vulnerability SLA visibility. Replaces monthly spreadsheet tracking with automated breach detection.

---

## DevSecOps Evidence Collector
*GitHub Action · Python · HMAC-SHA256 | [GitHub](https://github.com/sethodoiasare/grc-portfolio/tree/main/projects/04-devsecops-evidence-collector)*

Composite GitHub Action running SAST (Semgrep), SCA (pip-audit), secrets scanning (Gitleaks), and DAST (OWASP ZAP) in CI/CD. Maps findings to Vodafone DevSecOps D1-D8 controls. Produces cryptographically signed evidence packages.

**Why it matters:** CI/CD-native audit evidence. Cryptographically verifiable proof that security controls were executed — not just claimed.

---

## Cloud Posture Snapshot
*AWS · Azure · GCP · 52 CIS Benchmarks | [GitHub](https://github.com/sethodoiasare/grc-portfolio/tree/main/projects/05-cloud-posture-snapshot)*

CLI tool running CIS benchmark checks across all three major cloud providers. Mock mode requires zero credentials. Branded PDF reports with RAG scoring, management summaries, and Vodafone CYBER_038 control mappings.

**Why it matters:** Multi-cloud security posture in one command. Board-ready PDF in seconds.

---

## Policy-as-Code Starter Kit
*OPA/Rego · 12 Policies · Python Evaluator | [GitHub](https://github.com/sethodoiasare/grc-portfolio/tree/main/projects/06-policy-as-code)*

Production Rego policies for IAM least privilege, encryption enforcement, logging, and network security — with a pure-Python evaluator. Every policy mapped to a Vodafone control statement.

**Why it matters:** Bridges the gap between policy documentation and automated enforcement. OPA-ready.

---

## Security Metrics Pack
*MTTD/MTTR · Alert Quality · Vuln SLA · Matplotlib | [GitHub](https://github.com/sethodoiasare/grc-portfolio/tree/main/projects/07-security-metrics-pack)*

Computes security operations KPIs from incident, alert, and vulnerability records. Generates PNG charts. Multi-factor RAG scoring automatically surfaces the worst-performing area.

**Why it matters:** Replaces manual Excel-based security reporting with automated, reproducible metrics.

---

## Data Classification Scanner
*Regex · PII/PCI/PHI/Secrets Detection | [GitHub](https://github.com/sethodoiasare/grc-portfolio/tree/main/projects/08-data-classification-scanner)*

Scans files and directories for 14 categories of sensitive data — credit card PANs to AWS keys to private key headers. Context-aware false-positive filtering.

**Why it matters:** One-command sensitive data discovery. Finds secrets in config files before attackers do.

---

## Security Control Coverage Mapper
*PDF/DOCX Parsing · NLP · Fuzzy Matching | [GitHub](https://github.com/sethodoiasare/grc-portfolio)*

Parses policy documents (ISO 27001, NIST CSF), extracts control statements, maps them to implemented controls. Generates coverage heatmaps and gap analysis.

**Why it matters:** Answers the question every auditor asks first: "What controls do we have, and what's missing?"

---

## Risk Register + Scoring Engine
*CVSS v3.1 · SSVC · SQLite | [GitHub](https://github.com/sethodoiasare/grc-portfolio)*

Full CRUD risk register with dual scoring — CVSS for technical severity, SSVC for decision-driven prioritization. Risk acceptance workflows. PDF/CSV risk matrices.

**Why it matters:** Production-grade risk management. Aligned to ISO 27001 and NIST RMF.

---

## Vendor Security Questionnaire Scorer
*Excel/CSV Parsing · Weighted Scoring | [GitHub](https://github.com/sethodoiasare/grc-portfolio)*

Auto-scores completed vendor security questionnaires against configurable risk criteria. Generates vendor risk ratings with explainable rationale and remediation checklists.

**Why it matters:** Replaces days of manual questionnaire review with structured, defensible assessments.

---

## Incident Response Runbook Generator
*Claude API · YAML Templates · 6 Incident Types | [GitHub](https://github.com/sethodoiasare/grc-portfolio)*

Pre-built runbook templates for malware, ransomware, data breach, DDoS, insider threat, and credential theft. Claude API customizes each runbook to the specific incident.

**Why it matters:** Tailored incident response plans in seconds, not hours.

---

## Audit Readiness Dashboard
*Next.js · FastAPI · Cross-Project Aggregation | [GitHub](https://github.com/sethodoiasare/grc-portfolio)*

Web dashboard aggregating control status, evidence freshness, and audit deadlines across all projects. RAG-at-a-glance cards, deadline timeline, control coverage matrix.

**Why it matters:** Real-time audit preparedness visibility. Everything a CISO needs before walking into an audit committee.

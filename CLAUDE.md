@AGENTS.md

# gstack
- **gstack** (`~/.claude/skills/gstack/SKILL.md`) - engineering workflow toolkit
- Use the `/browse` skill from gstack for all web browsing tasks. Never use `mcp__claude-in-chrome__*` tools.
- Available gstack skills: `/office-hours`, `/plan-ceo-review`, `/plan-eng-review`, `/plan-design-review`, `/design-consultation`, `/design-shotgun`, `/design-html`, `/review`, `/ship`, `/land-and-deploy`, `/canary`, `/benchmark`, `/browse`, `/connect-chrome`, `/qa`, `/qa-only`, `/design-review`, `/setup-browser-cookies`, `/setup-deploy`, `/setup-gbrain`, `/retro`, `/investigate`, `/document-release`, `/codex`, `/cso`, `/autoplan`, `/plan-devex-review`, `/devex-review`, `/careful`, `/freeze`, `/guard`, `/unfreeze`, `/gstack-upgrade`, `/learn`.

# 🧠 Claude Project Ideas Roadmap
## Cybersecurity / GRC Engineering Portfolio

This document outlines a series of high-impact cybersecurity and GRC-focused projects designed to demonstrate deep technical capability, automation thinking, and real-world applicability.

These projects are intended to build on top of the **AI Control Assurance Engine** and evolve into a cohesive GRC intelligence ecosystem.

---

## 🔥 Core Philosophy

- Focus on **depth over breadth**
- Build **automation-first solutions**
- Ensure **real-world audit and security relevance**
- Prioritize **defensibility and explainability**
- Design for **modularity and extensibility**

---

## 📌 Project Ideas

---

### 1. 🗺️ Security Control Coverage Mapper

**Description:**
Parse policies and standards (e.g., ISO 27001, NIST CSF) and map them to implemented controls.

**Key Features:**
- Ingest policy documents (PDF, Word)
- Extract and normalize control statements
- Map to implemented controls
- Generate:
  - Coverage heatmap
  - Gap analysis report

**Outcome:**
Clear visibility into compliance coverage and control gaps.

---

### 2. 📂 Evidence Collection Automation

**Description:**
Automate the collection of audit evidence across systems.

**Key Features:**
- Scripts to collect:
  - Logs
  - Configurations
  - Screenshots
  - Asset inventories
- Normalize outputs into structured format
- Bundle into audit-ready packages

**Outcome:**
Reduces manual audit preparation effort significantly.

---

### 3. 📊 Risk Register + Scoring Engine

**Description:**
A lightweight but powerful risk management system.

**Key Features:**
- Risk register (CRUD operations)
- Risk scoring using:
  - CVSS
  - SSVC
- Risk acceptance workflows
- Exportable reports (PDF/CSV)

**Outcome:**
Quantifiable and structured risk management capability.

---

### 4. ☁️ Cloud Posture Snapshot

**Description:**
CLI-based tool to assess cloud security posture.

**Key Features:**
- AWS / Azure / GCP checks
- Identify misconfigurations
- Output:
  - JSON report
  - PDF summary

**Outcome:**
Quick, actionable cloud security insights.

---

### 5. 🧾 Vendor Security Questionnaire Scorer

**Description:**
Evaluate third-party vendor questionnaires automatically.

**Key Features:**
- Ingest completed questionnaires
- Score responses based on risk criteria
- Generate:
  - Risk rating
  - Rationale
  - Remediation checklist

**Outcome:**
Streamlined third-party risk assessment.

---

### 6. ⚖️ Policy-as-Code Starter Kit

**Description:**
Translate security policies into enforceable code.

**Key Features:**
- Open Policy Agent (OPA) examples
- Rego policies for:
  - IAM least privilege
  - Encryption enforcement
  - Logging requirements

**Outcome:**
Bridges gap between policy and enforcement.

---

### 7. 🚨 Incident Response Runbook Generator

**Description:**
Generate tailored incident response runbooks.

**Key Features:**
- Templates for different incident types
- AI-assisted customization
- Output structured runbooks

**Outcome:**
Faster and more consistent incident response preparation.

---

### 8. 📅 Audit Readiness Dashboard

**Description:**
Local web app to track audit readiness.

**Key Features:**
- Control status tracking
- Evidence freshness indicators
- Upcoming audit deadlines
- Visual dashboards

**Outcome:**
Real-time audit preparedness visibility.

---

### 9. 📈 Security Metrics Pack

**Description:**
Scripts to compute and visualize key security metrics.

**Key Features:**
- MTTD / MTTR calculations
- Alert quality metrics
- Vulnerability SLA tracking
- Trend analysis charts

**Outcome:**
Data-driven security performance insights.

---

### 10. 🔍 Data Classification Scanner

**Description:**
Scan files and classify sensitive data.

**Key Features:**
- Regex + NLP/NER-based detection
- Identify PII and sensitive data
- Generate classification reports

**Outcome:**
Improved data visibility and compliance readiness.

---

## 🧭 Execution Strategy

1. Build and finalize the **AI Control Assurance Engine** (flagship)
2. Expand into:
   - Evidence Collection Automation
   - Control Coverage Mapper
3. Gradually integrate other modules into a unified ecosystem

---

## 🚀 Long-Term Vision

Transform these projects into:

> **A unified, AI-powered GRC platform that automates assurance, risk, and compliance workflows end-to-end**

---

## ⚠️ Guiding Principle

Each project must:
- Solve a real problem
- Be demonstrable in a live demo
- Show clear business value
- Reflect senior-level thinking

---

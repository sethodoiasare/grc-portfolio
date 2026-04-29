"""Runbook generation engine.

Orchestrates template selection, AI customisation, and output formatting.
"""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .models import (
    Runbook, RunbookTemplate, IRStage, Severity, INCIDENT_TYPE_LABELS, SEVERITY_SLA,
)
from .templates import TEMPLATES
from .ai_customizer import customize_runbook, enrich_with_regulatory


def generate_runbook(
    incident_type: str,
    severity: str,
    context: dict | None = None,
) -> Runbook:
    """Full pipeline: select template, customise, assemble runbook.

    Args:
        incident_type: One of malware, ransomware, breach, ddos, insider, credential.
        severity: SEV1, SEV2, or SEV3.
        context: Organisation context dict (org_name, industry, regulatory_reqs, etc.).

    Returns:
        A fully assembled Runbook.
    """
    if context is None:
        context = {}

    template = TEMPLATES.get(incident_type)
    if template is None:
        raise ValueError(f"Unknown incident type: {incident_type}. Available: {list(TEMPLATES.keys())}")

    sev = Severity(severity)

    # Customise the template with AI
    customised = customize_runbook(template, context)

    # Adjust SLAs based on severity
    sla_overrides = SEVERITY_SLA.get(sev, SEVERITY_SLA[Severity.SEV2])
    stages: list[IRStage] = []
    for stage in customised["stages"]:
        adjusted_sla = _adjust_sla_for_severity(stage.sla_minutes, sev)
        stages.append(IRStage(
            stage_number=stage.stage_number,
            stage_name=stage.stage_name,
            description=stage.description,
            actions=stage.actions,
            responsible_team=stage.responsible_team,
            sla_minutes=adjusted_sla,
            escalation_trigger=stage.escalation_trigger,
        ))

    # Add regulatory actions to post-incident stages
    regs = context.get("regulatory_reqs", [])
    if regs:
        regulatory_actions = enrich_with_regulatory(regs)
        for stage in stages:
            if stage.stage_number == 5:  # Post-Incident Analysis
                stage.actions.extend(regulatory_actions[:4])
            elif stage.stage_number == 6:  # Lessons Learned
                stage.actions.extend(regulatory_actions[4:])

    # Build recovery objectives based on severity
    rto_hours = {Severity.SEV1: 4, Severity.SEV2: 8, Severity.SEV3: 24}.get(sev, 8)
    rpo_hours = {Severity.SEV1: 1, Severity.SEV2: 4, Severity.SEV3: 12}.get(sev, 4)

    org_name = context.get("org_name", "Organisation")

    runbook = Runbook(
        incident_type=incident_type,
        severity=sev,
        generated_date=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        organization=org_name,
        stages=stages,
        contacts=customised["contacts"],
        tools=customised["tools"],
        communication_plan=customised["communication_plan"],
        recovery_objectives={
            "rto_hours": rto_hours,
            "rpo_hours": rpo_hours,
        },
        lessons_learned_prompt=_build_lessons_learned_prompt(incident_type, severity, org_name),
    )

    return runbook


def generate_all(context: dict | None = None) -> list[Runbook]:
    """Generate all 6 runbooks for a given context."""
    runbooks: list[Runbook] = []
    for incident_type in TEMPLATES:
        # Use SEV2 as default for batch generation
        runbooks.append(generate_runbook(incident_type, "SEV2", context))
    return runbooks


def export_runbook_markdown(runbook: Runbook) -> str:
    """Export a runbook as a full markdown document.

    Includes headings, checkboxes for actions, tables for contacts/tools/SLAs,
    and structured sections that an incident responder can follow step by step.
    """
    sev = runbook.severity.value
    label = INCIDENT_TYPE_LABELS.get(runbook.incident_type, runbook.incident_type)
    sla = SEVERITY_SLA.get(runbook.severity, SEVERITY_SLA[Severity.SEV2])

    lines: list[str] = []
    lines.append(f"# Incident Response Runbook: {label}")
    lines.append("")
    lines.append(f"**Organisation:** {runbook.organization}  ")
    lines.append(f"**Incident Type:** {label}  ")
    lines.append(f"**Severity:** {sev}  ")
    lines.append(f"**Generated:** {runbook.generated_date}  ")
    lines.append(f"**Total Stages:** {len(runbook.stages)}  ")
    lines.append(f"**Total Actions:** {runbook.total_actions}  ")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Severity SLA summary
    lines.append("## Severity SLA")
    lines.append("")
    lines.append(f"| Metric | Target |")
    lines.append(f"|--------|--------|")
    lines.append(f"| Response Time | {sla['response']} minutes |")
    lines.append(f"| Containment Time | {sla['containment']} minutes |")
    lines.append(f"| Resolution Time | {sla['resolution']} minutes |")
    lines.append("")

    # Recovery Objectives
    lines.append("## Recovery Objectives")
    lines.append("")
    lines.append(f"- **Recovery Time Objective (RTO):** {runbook.recovery_objectives.get('rto_hours', 'N/A')} hours")
    lines.append(f"- **Recovery Point Objective (RPO):** {runbook.recovery_objectives.get('rpo_hours', 'N/A')} hours")
    lines.append("")

    # Contacts
    lines.append("## Key Contacts")
    lines.append("")
    lines.append(f"| Role | Name | Email | Phone |")
    lines.append(f"|------|------|-------|-------|")
    for role, info in runbook.contacts.items():
        lines.append(f"| {role} | {info.get('name', 'N/A')} | {info.get('email', 'N/A')} | {info.get('phone', 'N/A')} |")
    lines.append("")

    # Tools
    lines.append("## Tools & Systems")
    lines.append("")
    lines.append(f"| Tool | Purpose |")
    lines.append(f"|------|---------|")
    for tool in runbook.tools:
        lines.append(f"| {tool.get('name', 'N/A')} | {tool.get('purpose', 'N/A')} |")
    lines.append("")

    # Communication Plan
    lines.append("## Communication Plan")
    lines.append("")
    for comm in runbook.communication_plan:
        lines.append(f"- {comm}")
    lines.append("")

    # IR Stages
    lines.append("## Incident Response Stages")
    lines.append("")
    for stage in runbook.stages:
        lines.append(f"### Stage {stage.stage_number}: {stage.stage_name}")
        lines.append("")
        lines.append(f"**Description:** {stage.description}  ")
        lines.append(f"**Responsible Team:** {stage.responsible_team}  ")
        lines.append(f"**SLA:** {stage.sla_minutes} minutes  ")
        lines.append(f"**Escalation Trigger:** {stage.escalation_trigger}  ")
        lines.append("")
        lines.append("**Actions:**")
        lines.append("")
        for action in stage.actions:
            lines.append(f"- [ ] {action}")
        lines.append("")

    # Lessons Learned Prompt
    lines.append("## Lessons Learned")
    lines.append("")
    lines.append(runbook.lessons_learned_prompt)
    lines.append("")

    lines.append("---")
    lines.append(f"*Runbook generated by Incident Response Runbook Generator on {runbook.generated_date}*")
    lines.append("")

    return "\n".join(lines)


def export_runbook_json(runbook: Runbook) -> str:
    """Export a runbook as structured JSON."""
    return json.dumps(runbook.to_dict(), indent=2)


def save_runbook(runbook: Runbook, output_dir: Path, format: str = "both") -> list[Path]:
    """Save a runbook to the specified directory in markdown and/or JSON format.

    Args:
        runbook: The Runbook to save.
        output_dir: Directory to save files in.
        format: "md", "json", or "both".

    Returns:
        List of saved file paths.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    sev = runbook.severity.value.lower()
    incident_type = runbook.incident_type
    saved: list[Path] = []

    if format in ("md", "both"):
        md_path = output_dir / f"{incident_type}-{sev}-runbook.md"
        md_path.write_text(export_runbook_markdown(runbook))
        saved.append(md_path)

    if format in ("json", "both"):
        json_path = output_dir / f"{incident_type}-{sev}-runbook.json"
        json_path.write_text(export_runbook_json(runbook))
        saved.append(json_path)

    return saved


# ─────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────

def _adjust_sla_for_severity(base_sla: int, severity: Severity) -> int:
    """Adjust SLA minutes based on severity level."""
    if severity == Severity.SEV1:
        # SEV1: compress SLAs to 50% of base
        return max(5, int(base_sla * 0.5))
    elif severity == Severity.SEV3:
        # SEV3: relax SLAs to 150% of base
        return int(base_sla * 1.5)
    return base_sla


def _build_lessons_learned_prompt(incident_type: str, severity: str, org_name: str) -> str:
    """Build a structured lessons-learned prompt for post-incident review."""
    label = INCIDENT_TYPE_LABELS.get(incident_type, incident_type)

    prompts: dict[str, str] = {
        "malware": (
            f"Review the Malware Outbreak incident at {org_name} (Severity: {severity}). "
            "Document: (1) How did the malware enter the environment? "
            "(2) Which controls failed to detect it? "
            "(3) How effective was the containment -- did lateral movement occur? "
            "(4) Were backups clean and restorable? "
            "(5) What new IOCs should be added to detection tooling? "
            "(6) How can user awareness training be improved to reduce future risk?"
        ),
        "ransomware": (
            f"Review the Ransomware Attack incident at {org_name} (Severity: {severity}). "
            "Document: (1) What was the initial access vector? "
            "(2) How quickly was encryption detected and contained? "
            "(3) Was backup infrastructure protected from encryption? "
            "(4) Was data exfiltrated before encryption (double extortion)? "
            "(5) Was the ransom paid? If so, did decryption work? "
            "(6) What improvements are needed for offline/immutable backups, AD hardening, and email security?"
        ),
        "breach": (
            f"Review the Data Breach incident at {org_name} (Severity: {severity}). "
            "Document: (1) What data was exfiltrated and how was it accessed? "
            "(2) Were regulatory notification deadlines met (GDPR 72h, PCI-DSS 24h)? "
            "(3) Was the breached data encrypted at rest and in transit? "
            "(4) How effective were DLP controls at preventing exfiltration? "
            "(5) What was the root cause: misconfiguration, compromised credentials, insider, or application vulnerability? "
            "(6) What improvements are needed for data classification, access control, and monitoring?"
        ),
        "ddos": (
            f"Review the DDoS Attack incident at {org_name} (Severity: {severity}). "
            "Document: (1) What was the attack vector and peak volume? "
            "(2) How effective was the DDoS mitigation provider? "
            "(3) Were legitimate users able to access the service during mitigation? "
            "(4) What was the total downtime and estimated revenue impact? "
            "(5) Was there a companion attack (data breach, social engineering)? "
            "(6) Is current DDoS protection capacity adequate for future attacks?"
        ),
        "insider": (
            f"Review the Insider Threat incident at {org_name} (Severity: {severity}). "
            "Document: (1) What was the insider's motive and method? "
            "(2) What data or systems were affected? "
            "(3) Were HR trigger events missed that could have provided early warning? "
            "(4) How effective were UEBA, DLP, and access controls at detecting and preventing the incident? "
            "(5) Was the offboarding process executed completely and timely? "
            "(6) What improvements are needed for background checks, privilege management, and monitoring?"
        ),
        "credential": (
            f"Review the Credential Theft incident at {org_name} (Severity: {severity}). "
            "Document: (1) How were the credentials compromised (phishing, credential stuffing, MFA fatigue, token theft)? "
            "(2) What was the privilege level of the compromised account? "
            "(3) How quickly was the compromise detected and the account locked? "
            "(4) Did the attacker achieve lateral movement or persistence? "
            "(5) Was MFA bypassed or not enforced for the affected account? "
            "(6) What improvements are needed for MFA enforcement, password policy, breached password detection, and phishing-resistant authentication?"
        ),
    }

    return prompts.get(incident_type, f"Review the {label} incident at {org_name} (Severity: {severity}). Document root cause, control failures, response effectiveness, and improvement actions.")

"""AI-assisted runbook customisation.

Simulates a Claude API integration that tailors runbook templates to an
organisation's specific context: industry, regulatory requirements, threat
profile, and technology stack. All customisation happens via intelligent
template-string substitution with domain-aware defaults so the output
feels like a real AI-generated customisation.
"""

import copy
from .models import IRStage


# ─────────────────────────────────────────────────────────────────
# Regulatory enrichment
# ─────────────────────────────────────────────────────────────────

REGULATORY_ACTIONS: dict[str, list[str]] = {
    "GDPR": [
        "Log all incident response actions with GDPR Article 33/34 notification obligations in mind -- document every decision regarding notification timing",
        "Engage Data Protection Officer (DPO) immediately -- DPO must be involved in assessing whether the incident triggers 72-hour supervisory authority notification obligation",
        "Assess whether the incident constitutes a 'personal data breach' under GDPR Article 4(12) -- if yes, prepare notification to the relevant supervisory authority (ICO in UK, DPA in EU member state)",
        "Document legitimate interest or legal basis assessment for any data processing decisions made during incident response that differ from normal processing purposes",
        "Ensure all forensic evidence handling maintains data subject rights -- evidence containing personal data must be stored and processed in compliance with GDPR Article 5 principles",
        "Prepare data subject communication if the breach is likely to result in 'high risk to the rights and freedoms of natural persons' (Article 34) -- plain language, clear actions for affected individuals",
    ],
    "PCI-DSS": [
        "Engage PCI Qualified Security Assessor (QSA) if the incident affects the cardholder data environment (CDE) -- QSA guidance is required for PCI-compliant incident response",
        "Preserve all logs from CDE systems for at least 12 months as required by PCI-DSS Requirement 10.7 -- ensure log integrity via cryptographic hashing or write-once storage",
        "Notify acquiring bank and payment card brands within 24 hours if cardholder data (PAN, expiry, CVV, track data) is confirmed or suspected compromised",
        "Engage PCI Forensic Investigator (PFI) if card brand requires independent forensic investigation -- PFI findings directly impact potential fines and ongoing merchant status",
        "Review and update PCI-DSS scope documentation post-incident: any systems accessed by the attacker become 'in scope' for PCI assessment until validated clean",
        "Prepare for potential PCI-DSS re-assessment if the incident indicates a systemic control failure -- SAQ or ROC may need to be re-performed earlier than annual schedule",
    ],
    "NIS2": [
        "Notify the competent authority (e.g., ICO in UK for digital service providers, sector-specific regulator for essential entities) in accordance with NIS2 Article 23(4) -- initial notification within 24 hours, full report within 72 hours",
        "Assess whether the incident constitutes a 'significant incident' under NIS2 criteria: service disruption exceeding thresholds, affecting multiple member states, or involving malicious action",
        "Coordinate with supply chain partners if the incident originated from or affects a third-party service provider -- NIS2 Article 21 requires supply chain security management",
        "Engage the organisation's NIS2 compliance officer to ensure incident response documentation meets the regulator's template requirements for preliminary and final notification",
        "Review whether the incident triggers NIS2 Article 20 management body accountability -- senior management may need to approve incident response measures and be held accountable for compliance",
        "Document all risk management measures in place prior to the incident to demonstrate compliance with NIS2 Article 21(2) -- this may mitigate potential enforcement action",
    ],
    "SOX": [
        "Assess impact on IT General Controls (ITGCs) relevant to financial reporting: access management, change management, and computer operations controls that were bypassed or affected",
        "Engage external auditors (if integrated audit) to determine whether the incident requires disclosure under SOX Section 404 material weakness or significant deficiency framework",
        "Preserve all evidence of IT control operation during the incident period: access review records, change management tickets, privileged access logs, and SOD (segregation of duties) evidence",
        "Evaluate whether the incident affects the accuracy or completeness of financial data processed by affected systems -- if financial data integrity is compromised, this may require SOX 302/906 disclosure certification impact assessment",
        "Document compensating controls implemented during incident response that deviate from normal ITGC operation -- compensating controls must be validated by auditors for SOX compliance",
        "Coordinate with Internal Audit and external auditors on incident disclosure timing -- premature or incomplete disclosure to auditors can complicate SOX certification",
    ],
}


def enrich_with_regulatory(regs_list: list[str]) -> list[str]:
    """Return relevant compliance actions for a given list of regulations.

    Args:
        regs_list: List of regulation codes, e.g. ["GDPR", "PCI-DSS", "NIS2", "SOX"]

    Returns:
        List of compliance action strings relevant to the specified regulations.
    """
    actions: list[str] = []
    seen: set[str] = set()

    for reg in regs_list:
        reg = reg.upper().strip()
        if reg in REGULATORY_ACTIONS:
            for action in REGULATORY_ACTIONS[reg]:
                if action not in seen:
                    actions.append(f"[{reg}] {action}")
                    seen.add(action)

    return actions


# ─────────────────────────────────────────────────────────────────
# AI customisation engine (simulated Claude API)
# ─────────────────────────────────────────────────────────────────

def customize_runbook(template, context: dict):
    """Simulate AI-assisted customisation by injecting context-specific details.

    Takes a RunbookTemplate and a context dict, then returns a new template-like
    object with stages, contacts, tools, and comms enriched with organisation-
    specific information. No actual API call -- the simulation uses template-string
    substitution and intelligent defaults that vary meaningfully based on context.

    Args:
        template: A RunbookTemplate instance.
        context: Dict with keys: org_name, industry, regulatory_reqs, specific_threats,
                 tool_stack, cloud_provider, data_classification.

    Returns:
        A dict with keys: incident_type, stages (list of IRStage dicts), contacts (dict),
        tools (list of dicts), communication_plan (list of str).
    """
    org_name = context.get("org_name", "Organisation")
    industry = context.get("industry", "General")
    tool_stack = context.get("tool_stack", [])
    regs = context.get("regulatory_reqs", [])
    threats = context.get("specific_threats", [])
    cloud = context.get("cloud_provider", "AWS")

    # Deep-copy stages and inject context
    stages: list[IRStage] = []
    for stage in template.base_stages:
        new_actions: list[str] = []
        for action in stage.actions:
            # Replace generic placeholders with context-specific references
            modified = action
            # Inject org name into generic references
            modified = modified.replace("company.com", f"{org_name.lower().replace(' ', '-')}.com")
            # Inject tool references from context
            if tool_stack:
                modified = _inject_tool_references(modified, tool_stack, cloud)
            # Inject regulatory context into relevant stages
            if regs and stage.stage_number in (5, 6):
                modified = _inject_regulatory_context(modified, regs, org_name)
            # Inject threat intelligence context
            if threats and stage.stage_number in (1, 5):
                modified = _inject_threat_context(modified, threats, org_name)
            new_actions.append(modified)

        # Add context-specific actions at key stages
        if stage.stage_number == 1 and industry:
            new_actions.append(
                f"Consider {industry}-specific threat intelligence sources and sector ISAC feeds for contextualised detection"
            )
        if stage.stage_number == 6 and regs:
            reg_labels = ", ".join(regs)
            new_actions.append(
                f"Schedule regulatory compliance review with {org_name} compliance team covering: {reg_labels}"
            )

        new_stage = IRStage(
            stage_number=stage.stage_number,
            stage_name=stage.stage_name,
            description=stage.description,
            actions=new_actions,
            responsible_team=stage.responsible_team.replace(
                "company.com", f"{org_name.lower().replace(' ', '-')}.com"
            ),
            sla_minutes=stage.sla_minutes,
            escalation_trigger=stage.escalation_trigger,
        )
        stages.append(new_stage)

    # Customise contacts
    org_domain = f"{org_name.lower().replace(' ', '').replace('ltd', '').replace('limited', '').replace('llc', '').replace('inc', '').strip()}.com"
    contacts: dict[str, dict] = {}
    for role, info in template.default_contacts.items():
        new_info = dict(info)
        new_info["email"] = new_info["email"].replace("company.com", org_domain)
        contacts[role] = new_info

    # Customise tools -- inject user's actual tool stack where it overlaps with defaults
    tools: list[dict] = list(template.default_tools)
    if tool_stack:
        for user_tool in tool_stack:
            tool_name = user_tool.get("name", "")
            if tool_name and not any(t["name"].lower() == tool_name.lower() for t in tools):
                tools.append({"name": tool_name, "purpose": user_tool.get("purpose", "User-specified tool")})

    # Customise communication plan
    comms: list[str] = []
    for comm in template.default_comms:
        modified = comm.replace("company.com", org_domain)
        comms.append(modified)

    # Add context-specific comms
    if regs:
        reg_list = ", ".join(regs)
        comms.append(
            f"Regulatory notification tracking: {org_name} compliance team maintains log of all {reg_list} notification deadlines, submissions, and regulator correspondence during the incident"
        )
    if industry:
        comms.append(
            f"Industry-specific disclosure: coordinate with {org_name} Industry Relations team to assess whether sector-specific reporting obligations apply"
        )

    return {
        "incident_type": template.incident_type,
        "stages": stages,
        "contacts": contacts,
        "tools": tools,
        "communication_plan": comms,
    }


def _inject_tool_references(action: str, tool_stack: list[dict], cloud: str) -> str:
    """Inject user's actual tool names into action descriptions where generic names appear."""
    tool_map = _build_tool_substitution_map(tool_stack, cloud)
    for generic, specific in tool_map.items():
        if generic.lower() in action.lower():
            # Replace once, preferring the first occurrence
            action = _replace_case_insensitive(action, generic, specific)
    return action


def _build_tool_substitution_map(tool_stack: list[dict], cloud: str) -> dict[str, str]:
    """Build a mapping from generic tool names to user's specific tools."""
    mappings: dict[str, str] = {}

    tool_by_category: dict[str, str] = {}
    for t in tool_stack:
        name = t.get("name", "")
        purpose = t.get("purpose", "").lower()

        if "edr" in purpose or "endpoint" in purpose or "falcon" in name.lower():
            tool_by_category["edr"] = name
        elif "siem" in purpose or "splunk" in name.lower() or "sentinel" in name.lower():
            tool_by_category["siem"] = name
        elif "identity" in purpose or "okta" in name.lower() or "azure ad" in name.lower() or "entra" in name.lower():
            tool_by_category["idp"] = name
        elif "pagerduty" in name.lower() or "opsgenie" in name.lower() or "victorops" in name.lower():
            tool_by_category["pager"] = name
        elif "dlp" in purpose or "symantec" in name.lower() or "forcepoint" in name.lower() or "zscaler" in name.lower():
            tool_by_category["dlp"] = name
        elif "waf" in purpose or "cloudflare" in name.lower() or "akamai" in name.lower():
            tool_by_category["ddos"] = name
        elif "backup" in purpose or "veeam" in name.lower() or "rubrik" in name.lower():
            tool_by_category["backup"] = name
        elif "pam" in purpose or "cyberark" in name.lower() or "beyondtrust" in name.lower() or "delinea" in name.lower():
            tool_by_category["pam"] = name

    if "edr" in tool_by_category:
        mappings["CrowdStrike Falcon"] = tool_by_category["edr"]
        mappings["CrowdStrike"] = tool_by_category["edr"]
        mappings["SentinelOne"] = tool_by_category["edr"]
        mappings["Defender"] = tool_by_category["edr"]
    if "siem" in tool_by_category:
        mappings["Splunk"] = tool_by_category["siem"]
        mappings["Sentinel"] = tool_by_category["siem"]
        mappings["SIEM"] = tool_by_category["siem"]
    if "idp" in tool_by_category:
        mappings["Okta"] = tool_by_category["idp"]
        mappings["Azure AD"] = tool_by_category["idp"]
        mappings["Active Directory"] = f"{tool_by_category['idp']} / Active Directory"
    if "pager" in tool_by_category:
        mappings["PagerDuty"] = tool_by_category["pager"]
    if "dlp" in tool_by_category:
        mappings["DLP Platform"] = tool_by_category["dlp"]
        mappings["Symantec"] = tool_by_category["dlp"]
        mappings["Forcepoint"] = tool_by_category["dlp"]
        mappings["Zscaler"] = tool_by_category["dlp"]
    if "ddos" in tool_by_category:
        mappings["Cloudflare"] = tool_by_category["ddos"]
        mappings["Akamai"] = tool_by_category["ddos"]
        mappings["AWS Shield"] = tool_by_category["ddos"]
    if "backup" in tool_by_category:
        mappings["Veeam"] = tool_by_category["backup"]
        mappings["Rubrik"] = tool_by_category["backup"]

    return mappings


def _replace_case_insensitive(text: str, old: str, new: str) -> str:
    """Replace first case-insensitive occurrence of old with new."""
    idx = text.lower().find(old.lower())
    if idx == -1:
        return text
    return text[:idx] + new + text[idx + len(old):]


def _inject_regulatory_context(action: str, regs: list[str], org_name: str) -> str:
    """Append regulatory context to relevant post-incident actions."""
    if "GDPR" in [r.upper() for r in regs] and "data" in action.lower():
        action += f" -- ensure GDPR Article 33/34 obligations for {org_name} are discharged within statutory timeframes"
    if "PCI-DSS" in [r.upper() for r in regs] and ("cardholder" in action.lower() or "payment" in action.lower() or "CDE" in action.upper()):
        action += f" -- coordinate with {org_name} PCI QSA for compliance-validated incident handling"
    return action


def _inject_threat_context(action: str, threats: list[str], org_name: str = "the organisation") -> str:
    """Add threat-specific awareness to detection actions."""
    if len(threats) <= 2:
        threat_str = " and ".join(threats)
        if "detect" in action.lower() or "identif" in action.lower() or "triage" in action.lower():
            action += f" -- pay special attention to indicators of {threat_str} based on {org_name} threat profile"
    return action

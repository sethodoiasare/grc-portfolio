"""Coverage mapping engine — fuzzy match parsed controls against known frameworks."""

import re
from collections import Counter
from typing import Optional

from .models import ControlStatement, CoverageResult, CoverageStatus


# Thresholds for similarity-based classification
HIGH_SIMILARITY = 0.40
MEDIUM_SIMILARITY = 0.20


def map_coverage(
    parsed_controls: list[ControlStatement],
    framework_controls: list[ControlStatement],
) -> CoverageResult:
    """Map parsed policy controls against a framework and produce a CoverageResult.

    Each framework control is compared against all parsed controls using token-based
    similarity (Jaccard with keyword boost). The best match determines status:
      - COVERED: high similarity match found
      - PARTIAL: medium similarity match found
      - GAP: no match above threshold
    """
    result_controls = []
    covered = partial = gap = 0

    for fw_ctrl in framework_controls:
        best_score = 0.0
        best_match: Optional[ControlStatement] = None

        for parsed_ctrl in parsed_controls:
            score = _similarity(fw_ctrl, parsed_ctrl)
            if score > best_score:
                best_score = score
                best_match = parsed_ctrl

        status: CoverageStatus
        if best_score >= HIGH_SIMILARITY:
            status = CoverageStatus.COVERED
            covered += 1
        elif best_score >= MEDIUM_SIMILARITY:
            status = CoverageStatus.PARTIAL
            partial += 1
        else:
            status = CoverageStatus.GAP
            gap += 1

        result_ctrl = ControlStatement(
            framework=fw_ctrl.framework,
            control_id=fw_ctrl.control_id,
            title=fw_ctrl.title,
            description=fw_ctrl.description,
            category=fw_ctrl.category,
            status=status,
            matched_text=best_match.description if best_match else None,
            similarity_score=round(best_score, 3),
        )
        result_controls.append(result_ctrl)

    heatmap = build_heatmap_data(result_controls)
    gaps_list = [c for c in result_controls if c.status == CoverageStatus.GAP]

    return CoverageResult(
        framework=framework_controls[0].framework,
        total_controls=len(framework_controls),
        covered=covered,
        partial=partial,
        gap=gap,
        gaps_list=gaps_list,
        heatmap_data=heatmap,
        controls=result_controls,
    )


def _tokenize(text: str) -> set[str]:
    """Tokenize text into lowercase word-level tokens, stripping punctuation."""
    tokens = re.findall(r"[a-z0-9]{3,}", text.lower())
    return set(tokens)


# Keyword groups that boost similarity when overlapping between framework and policy
_KEYWORD_GROUPS = {
    "access control": {"access", "privileged", "authentication", "mfa", "password", "credential"},
    "monitoring": {"log", "monitor", "siem", "alert", "detect", "audit", "correlate"},
    "encryption": {"encrypt", "aes", "tls", "key", "cryptographic", "cipher"},
    "endpoint": {"endpoint", "malware", "anti-virus", "antivirus", "host", "laptop", "desktop"},
    "network": {"network", "firewall", "segment", "vpn", "ssh", "rdp", "port"},
    "vulnerability": {"vulnerability", "patch", "scan", "remediate"},
    "incident response": {"incident", "response", "breach", "forensic", "containment"},
    "cloud": {"cloud", "aws", "azure", "gcp", "s3", "blob", "cspm"},
    "supplier": {"supplier", "vendor", "third-party", "third party", "outsource"},
    "business continuity": {"continuity", "disaster", "recovery", "dr", "bcdr"},
    "hr": {"background", "screening", "confidentiality", "nda", "personnel", "employee"},
    "development": {"sdlc", "development", "devsecops", "ci/cd", "pipeline", "static analysis"},
    "data protection": {"classification", "dlp", "data leakage", "exfiltration", "pii"},
    "asset": {"asset", "inventory", "hardware", "software", "licence", "license"},
    "governance": {"policy", "governance", "ciso", "management", "approve", "review"},
}


def _keyword_boost(tokens_a: set[str], tokens_b: set[str]) -> float:
    """Return a similarity boost when both sets contain domain keywords."""
    boost = 0.0
    for _group_name, keywords in _KEYWORD_GROUPS.items():
        a_hits = tokens_a & keywords
        b_hits = tokens_b & keywords
        if a_hits and b_hits:
            boost += 0.05 * min(len(a_hits), len(b_hits))
    return min(boost, 0.30)  # Cap at 0.30


def _similarity(a: ControlStatement, b: ControlStatement) -> float:
    """Compute token-based similarity score between two controls.

    Uses Jaccard coefficient on tokenised control descriptions, plus a keyword
    domain-overlap boost. The boost rewards controls that share security-domain
    vocabulary even when the exact tokens differ.
    """
    text_a = f"{a.title} {a.description} {a.category} {a.control_id}"
    text_b = f"{b.title} {b.description} {b.category}"

    tokens_a = _tokenize(text_a)
    tokens_b = _tokenize(text_b)

    if not tokens_a or not tokens_b:
        return 0.0

    intersection = tokens_a & tokens_b
    union = tokens_a | tokens_b
    jaccard = len(intersection) / len(union)

    boost = _keyword_boost(tokens_a, tokens_b)
    return min(jaccard + boost, 1.0)


def build_heatmap_data(controls: list[ControlStatement]) -> dict:
    """Build heatmap data by category."""
    categories: dict[str, dict] = {}
    for c in controls:
        cat = c.category or "Uncategorised"
        if cat not in categories:
            categories[cat] = {"total": 0, "covered": 0, "partial": 0, "gap": 0}
        categories[cat]["total"] += 1
        if c.status == CoverageStatus.COVERED:
            categories[cat]["covered"] += 1
        elif c.status == CoverageStatus.PARTIAL:
            categories[cat]["partial"] += 1
        else:
            categories[cat]["gap"] += 1

    heatmap = {}
    for cat, counts in categories.items():
        t = counts["total"]
        heatmap[cat] = {
            "total": t,
            "coverage_pct": round(counts["covered"] / t * 100, 1) if t else 0,
            "covered": counts["covered"],
            "partial": counts["partial"],
            "gap": counts["gap"],
        }
    return heatmap


_REMEDIATION_TEMPLATES = {
    "Access Control": "Add policy language defining formal access request, approval, provisioning, and periodic review processes. Reference privileged access management tooling.",
    "Endpoint Security": "Document endpoint protection requirements: anti-malware, host firewall, disk encryption, and MDM enrollment for mobile devices.",
    "Network Security": "Define network segmentation architecture, firewall rule management, and secure administrative access requirements.",
    "Cloud Security": "Specify cloud hardening standards (e.g., CIS benchmarks), encryption requirements, and CSPM monitoring.",
    "Vulnerability Management": "Establish vulnerability scanning cadence, patch SLA timelines for each severity tier, and escalation procedures.",
    "Security Monitoring": "Detail SIEM log collection scope, correlation rules, alert triage SLAs, and analyst response procedures.",
    "Incident Response": "Document incident response plan: roles, communication paths, containment procedures, and post-incident review requirements.",
    "Supplier Security": "Define third-party risk assessment criteria, ongoing monitoring requirements, and data access restrictions for suppliers.",
    "Business Continuity": "Document BCP/DR plan testing cadence, recovery time objectives, and annual review requirements.",
    "Governance": "Define policy management lifecycle: approval authority, review cadence, exception handling, and communication requirements.",
    "HR Security": "Document pre-employment screening scope, confidentiality agreement requirements, and employee offboarding procedures.",
    "Asset Management": "Define asset inventory requirements, classification levels, handling procedures, and asset disposal processes.",
    "Development": "Document secure SDLC requirements: code review, static analysis, security testing, and CI/CD separation of duties.",
    "Data Protection": "Define data classification scheme, encryption standards, DLP controls, and data handling procedures.",
    "Monitoring": "Detail monitoring scope, event correlation requirements, alert thresholds, and 24/7 coverage expectations.",
}


def generate_remediation(category: str) -> str:
    """Return a remediation suggestion for a given control category."""
    for key, template in _REMEDIATION_TEMPLATES.items():
        if key.lower() in category.lower():
            return template
    return "Add explicit policy language addressing this control area with measurable requirements and defined responsibilities."

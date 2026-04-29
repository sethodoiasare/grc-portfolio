"""Report generation: ASCII matrix, summaries, JSON/CSV export."""

import csv
import json
from io import StringIO
from pathlib import Path
from datetime import date
from collections import Counter

from .models import Risk, RiskRegister, RiskLevel
from .register import get_risk_matrix
from .cvss_calc import get_severity
from .ssvc_calc import ssvc_to_action


# Risk level colour markers (no emoji, ANSI-friendly)
_LEVEL_MARKER = {
    "CRITICAL": "!!",
    "HIGH": "! ",
    "MEDIUM": "~ ",
    "LOW": ". ",
}


def print_risk_matrix(register: RiskRegister) -> str:
    """Generate an ASCII 5x5 risk matrix heatmap.

    Returns the formatted string (also prints it).
    """
    matrix = get_risk_matrix(register)
    cells = matrix["cells"]

    # Labels for matrix zones
    zone_labels = {
        (0, 0): "LOW", (0, 1): "LOW", (1, 0): "LOW", (1, 1): "LOW",
        (0, 2): "MED", (1, 2): "MED", (2, 0): "MED", (2, 1): "MED",
        (0, 3): "MED", (1, 3): "HIGH", (2, 2): "MED", (3, 0): "MED",
        (3, 1): "MED", (2, 3): "HIGH", (3, 2): "HIGH", (0, 4): "HIGH",
        (1, 4): "HIGH", (4, 0): "MED", (4, 1): "MED", (2, 4): "CRIT",
        (3, 3): "HIGH", (4, 2): "HIGH", (3, 4): "CRIT", (4, 3): "CRIT",
        (4, 4): "CRIT",
    }

    lines = []
    lines.append("")
    lines.append("  RISK MATRIX (5x5) — Likelihood vs Impact")
    lines.append("  " + "=" * 55)
    lines.append("")
    lines.append("  IMPACT ->    1       2       3       4       5")
    lines.append("  LIKELIHOOD   VeryLow  Low    Medium  High   VeryHigh")
    lines.append("  " + "-" * 55)

    for li in range(4, -1, -1):  # Top-down: high likelihood first
        row_cells = []
        for im in range(5):
            count = cells[li][im]
            zone = zone_labels.get((li, im), "MED")
            if count > 0:
                row_cells.append(f"[{zone:>4}:{count:>2}]")
            else:
                row_cells.append(f"[  .  ]")
        label = f"L{li + 1}"
        lines.append(f"  {label}  " + "  ".join(row_cells))

    lines.append("  " + "-" * 55)
    lines.append("")

    total = sum(sum(row) for row in cells)
    lines.append(f"  Total risks: {total}")
    lines.append("")

    output = "\n".join(lines)
    print(output)
    return output


def print_risk_summary(register: RiskRegister) -> str:
    """Print a summary of the risk register by level, category, and status.

    Returns the formatted string (also prints it).
    """
    lines = []
    lines.append("")
    lines.append("  RISK REGISTER SUMMARY")
    lines.append("  " + "=" * 55)
    lines.append("")

    # By risk level
    level_counts = Counter(r.risk_level.value for r in register.risks)
    lines.append("  By Risk Level:")
    for level in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
        count = level_counts.get(level, 0)
        marker = _LEVEL_MARKER.get(level, "  ")
        bar = "#" * min(count, 40)
        lines.append(f"    {marker} {level:<10}: {count:>3}  {bar}")
    lines.append(f"    {'─' * 45}")
    lines.append(f"    {'TOTAL':<12}: {len(register.risks):>3}")
    lines.append("")

    # By category
    cat_counts = Counter(r.category.value for r in register.risks)
    lines.append("  By Category:")
    for cat, count in sorted(cat_counts.items()):
        lines.append(f"    {cat:<20}: {count:>3}")
    lines.append("")

    # By status
    status_counts = Counter(r.status.value for r in register.risks)
    lines.append("  By Status:")
    for status, count in sorted(status_counts.items()):
        lines.append(f"    {status:<20}: {count:>3}")
    lines.append("")

    # Top risks
    lines.append("  Top Risks by CVSS Score:")
    sorted_risks = sorted(register.risks, key=lambda r: r.cvss_score, reverse=True)
    for r in sorted_risks[:5]:
        marker = _LEVEL_MARKER.get(r.risk_level.value, "  ")
        lines.append(
            f"    {marker} {r.risk_id}  CVSS {r.cvss_score:<4}  "
            f"SSVC {r.ssvc_decision.value:<10}  {r.title[:50]}"
        )
    lines.append("")

    output = "\n".join(lines)
    print(output)
    return output


def print_risk_detail(risk: Risk) -> str:
    """Print a single risk in card format.

    Returns the formatted string (also prints it).
    """
    marker = _LEVEL_MARKER.get(risk.risk_level.value, "  ")
    sev = get_severity(risk.cvss_score)
    action = ssvc_to_action(risk.ssvc_decision)

    lines = []
    lines.append("")
    lines.append(f"  {'=' * 60}")
    lines.append(f"  {marker} RISK: {risk.risk_id} — {risk.title}")
    lines.append(f"  {'=' * 60}")
    lines.append(f"  Status:       {risk.status.value}")
    lines.append(f"  Category:     {risk.category.value}")
    lines.append(f"  Owner:        {risk.owner or '(unassigned)'}")
    lines.append(f"  Identified:   {risk.identified_date}")
    lines.append(f"  Risk Level:   {risk.risk_level.value}")
    lines.append(f"  Impact:       {risk.impact_score}/100")
    lines.append(f"  Likelihood:   {risk.likelihood_score}/100")
    lines.append(f"  CVSS Score:   {risk.cvss_score} ({sev})")
    lines.append(f"  CVSS Vector:  {risk.cvss_vector}")
    lines.append(f"  SSVC Decision:{risk.ssvc_decision.value}")
    lines.append(f"  SSVC Action:  {action[:80]}...")
    if risk.acceptance_rationale:
        lines.append(f"  Acceptance:   {risk.acceptance_rationale[:100]}")
    if risk.treatment_plan:
        lines.append(f"  Treatment:    {risk.treatment_plan[:100]}")
    if risk.review_date:
        overdue = " [OVERDUE]" if risk.review_date < date.today() else ""
        lines.append(f"  Review Date:  {risk.review_date}{overdue}")
    if risk.control_mapping:
        lines.append(f"  Controls:     {', '.join(risk.control_mapping)}")
    lines.append(f"  Description:  {risk.description[:200]}")
    lines.append(f"  {'=' * 60}")
    lines.append("")

    output = "\n".join(lines)
    print(output)
    return output


def save_register_json(register: RiskRegister, path: Path) -> Path:
    """Export the full risk register as JSON.

    Args:
        register: The RiskRegister to export.
        path: Output file path.

    Returns:
        The path written.
    """
    data = {
        "metadata": {
            "created": register.created,
            "updated": register.updated,
            "owner": register.owner,
            "total_risks": len(register.risks),
        },
        "risks": [],
    }
    for risk in register.risks:
        risk_dict = {
            "risk_id": risk.risk_id,
            "title": risk.title,
            "description": risk.description,
            "category": risk.category.value,
            "owner": risk.owner,
            "identified_date": risk.identified_date.isoformat(),
            "status": risk.status.value,
            "cvss_score": risk.cvss_score,
            "cvss_vector": risk.cvss_vector,
            "ssvc_decision": risk.ssvc_decision.value,
            "impact_score": risk.impact_score,
            "likelihood_score": risk.likelihood_score,
            "risk_level": risk.risk_level.value,
            "acceptance_rationale": risk.acceptance_rationale,
            "treatment_plan": risk.treatment_plan,
            "review_date": risk.review_date.isoformat() if risk.review_date else None,
            "control_mapping": risk.control_mapping,
        }
        data["risks"].append(risk_dict)

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))
    return path


def save_register_csv(register: RiskRegister, path: Path) -> Path:
    """Export the full risk register as CSV.

    Args:
        register: The RiskRegister to export.
        path: Output file path.

    Returns:
        The path written.
    """
    fieldnames = [
        "risk_id", "title", "description", "category", "owner",
        "identified_date", "status", "cvss_score", "cvss_vector",
        "ssvc_decision", "impact_score", "likelihood_score", "risk_level",
        "acceptance_rationale", "treatment_plan", "review_date", "control_mapping",
    ]

    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for risk in register.risks:
            row = {
                "risk_id": risk.risk_id,
                "title": risk.title,
                "description": risk.description,
                "category": risk.category.value,
                "owner": risk.owner,
                "identified_date": risk.identified_date.isoformat(),
                "status": risk.status.value,
                "cvss_score": risk.cvss_score,
                "cvss_vector": risk.cvss_vector,
                "ssvc_decision": risk.ssvc_decision.value,
                "impact_score": risk.impact_score,
                "likelihood_score": risk.likelihood_score,
                "risk_level": risk.risk_level.value,
                "acceptance_rationale": risk.acceptance_rationale or "",
                "treatment_plan": risk.treatment_plan or "",
                "review_date": risk.review_date.isoformat() if risk.review_date else "",
                "control_mapping": ";".join(risk.control_mapping),
            }
            writer.writerow(row)
    return path

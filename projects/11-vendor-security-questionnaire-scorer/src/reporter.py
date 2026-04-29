"""Output generators — terminal, JSON, and Markdown reports."""

import json
from pathlib import Path

from .models import VendorAssessment, RiskRating


RISK_COLORS = {
    RiskRating.LOW: "\033[92m",       # green
    RiskRating.MEDIUM: "\033[93m",    # yellow
    RiskRating.HIGH: "\033[91m",      # red (bright)
    RiskRating.CRITICAL: "\033[91m",  # red
}
RESET = "\033[0m"
BOLD = "\033[1m"


def print_assessment(assessment: VendorAssessment) -> None:
    """Print a formatted terminal assessment."""
    color = RISK_COLORS.get(assessment.risk_rating, "")
    total_questions = len(assessment.questions)
    scored_questions = sum(1 for q in assessment.questions if q.is_scored())
    na_count = total_questions - scored_questions

    print(f"\n{BOLD}{'='*70}{RESET}")
    print(f"{BOLD}  VENDOR SECURITY ASSESSMENT{RESET}")
    print(f"{BOLD}{'='*70}{RESET}")
    print(f"  Vendor:        {assessment.vendor_name}")
    print(f"  Date:          {assessment.assessment_date}")
    print(f"  Questions:     {total_questions} total ({scored_questions} scored, {na_count} N/A)")
    print(f"  Overall Score: {color}{assessment.overall_score:.1f}%{RESET}")
    print(f"  Risk Rating:   {color}{BOLD}{assessment.risk_rating.value}{RESET}")
    print(f"{'='*70}")

    print(f"\n{BOLD}  CATEGORY BREAKDOWN{RESET}")
    print(f"  {'Category':<22} {'Score':>7}  {'Max':>7}  {'Pct':>7}  Rating")
    print(f"  {'-'*22} {'-'*7}  {'-'*7}  {'-'*7}  {'-'*10}")
    for cs in assessment.category_scores:
        c = RISK_COLORS.get(cs.risk_level, "")
        print(f"  {cs.category:<22} {cs.total_weighted:>7.1f}  {cs.max_possible:>7.1f}  {cs.pct:>6.1f}%  {c}{cs.risk_level.value:<10}{RESET}")

    if assessment.top_risks:
        print(f"\n{BOLD}  TOP RISKS ({len(assessment.top_risks)}){RESET}")
        for risk in assessment.top_risks:
            print(f"    {RISK_COLORS[RiskRating.HIGH]}[!]{RESET} {risk}")

    if assessment.remediation_checklist:
        print(f"\n{BOLD}  REMEDIATION CHECKLIST{RESET}")
        print(f"  ({len(assessment.remediation_checklist)} total items — showing first 5)")
        for item in assessment.remediation_checklist[:5]:
            print(f"    - {item}")
        if len(assessment.remediation_checklist) > 5:
            print(f"    ... and {len(assessment.remediation_checklist) - 5} more items.")

    print(f"\n{BOLD}{'='*70}{RESET}\n")


def save_report_json(assessment: VendorAssessment, path: str) -> str:
    """Save the full assessment as a JSON file."""
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    data = assessment.to_dict()
    out.write_text(json.dumps(data, indent=2, default=str))
    return str(out)


def save_report_md(assessment: VendorAssessment, path: str) -> str:
    """Save the assessment as a Markdown report."""
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = []
    lines.append(f"# Vendor Security Assessment: {assessment.vendor_name}")
    lines.append("")
    lines.append(f"**Date:** {assessment.assessment_date}  ")
    lines.append(f"**Overall Score:** {assessment.overall_score:.1f}%  ")
    lines.append(f"**Risk Rating:** **{assessment.risk_rating.value}**  ")
    lines.append("")

    total = len(assessment.questions)
    scored = sum(1 for q in assessment.questions if q.is_scored())
    lines.append(f"*{total} questions ({scored} scored, {total - scored} N/A)*")
    lines.append("")

    lines.append("## Category Breakdown")
    lines.append("")
    lines.append("| Category | Score | Max | Pct | Rating |")
    lines.append("|----------|------:|----:|----:|--------|")
    for cs in assessment.category_scores:
        lines.append(f"| {cs.category} | {cs.total_weighted:.1f} | {cs.max_possible:.1f} | {cs.pct:.1f}% | {cs.risk_level.value} |")
    lines.append("")

    if assessment.top_risks:
        lines.append("## Top Risks")
        lines.append("")
        for risk in assessment.top_risks:
            lines.append(f"- {risk}")
        lines.append("")

    if assessment.remediation_checklist:
        lines.append("## Remediation Checklist")
        lines.append("")
        for item in assessment.remediation_checklist:
            lines.append(f"- {item}")
        lines.append("")

    out.write_text("\n".join(lines))
    return str(out)

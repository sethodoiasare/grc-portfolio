"""Report generation for IAM Access Lifecycle Simulator.

Produces structured violation reports and access certification packs.
"""

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

from .models import (
    AuditReport, Violation, Severity, SEVERITY_SLA,
)


def generate_access_certification(violations: list[Violation]) -> list[dict]:
    """Produce access certification items with REVOKE/REVIEW/CONFIRM actions
    and certify-by dates based on severity SLA."""
    items: list[dict] = []

    for v in violations:
        sla = SEVERITY_SLA.get(v.severity, {"days": 30})
        if "hours" in sla:
            certify_by = datetime.now(timezone.utc) + timedelta(hours=sla["hours"])
        else:
            certify_by = datetime.now(timezone.utc) + timedelta(days=sla.get("days", 30))

        action = _determine_action(v)

        items.append({
            "violation_id": v.violation_id,
            "type": v.type.value,
            "severity": v.severity.value,
            "description": v.description,
            "affected_accounts": v.affected_accounts,
            "control_id": v.control_mapping.get("control_id", ""),
            "action": action,
            "certify_by": certify_by.isoformat(),
            "certified_by": "",
            "remediation": v.remediation,
        })

    return items


def _determine_action(violation: Violation) -> str:
    """Map violation type to a certification action."""
    type_action = {
        "LEAVER_ACTIVE": "REVOKE",
        "ORPHANED": "REVOKE",
        "MFA_MISSING": "REVIEW",
        "SELF_APPROVAL": "REVIEW",
    }
    return type_action.get(violation.type.value, "REVIEW")


def format_summary(violations: list[Violation]) -> dict:
    """Count violations by severity and type."""
    by_severity = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0}
    by_type: dict[str, int] = {}

    for v in violations:
        by_severity[v.severity.value] += 1
        t = v.type.value
        by_type[t] = by_type.get(t, 0) + 1

    return {
        "total": len(violations),
        "by_severity": by_severity,
        "by_type": by_type,
    }


def build_audit_report(
    violations: list[Violation],
    ad_count: int,
    hr_count: int,
    itsm_count: int,
) -> AuditReport:
    """Build the full AuditReport from violations and scope info."""
    summary = format_summary(violations)
    cert_items = generate_access_certification(violations)

    return AuditReport(
        audit_date=datetime.now(timezone.utc).isoformat(),
        scope=f"{ad_count} AD accounts, {hr_count} HR records, {itsm_count} ITSM tickets reviewed",
        summary=summary,
        violations=violations,
        access_certification_items=cert_items,
    )


def export_json(report: AuditReport, output_path: Path) -> Path:
    """Export the audit report as structured JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    data = report.to_dict()
    output_path.write_text(json.dumps(data, indent=2, default=str))
    return output_path

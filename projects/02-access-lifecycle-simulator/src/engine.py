"""Violation detection engine for IAM Access Lifecycle Simulator."""

import uuid
from datetime import datetime, timezone
from typing import Optional

from .models import (
    ADUser, HREmployee, ITSMTicket,
    Violation, ViolationType, Severity,
    CONTROL_MAPPING,
)


def _make_violation(vtype: ViolationType, severity: Severity,
                    description: str, affected: list[str],
                    remediation: str) -> Violation:
    mapping = CONTROL_MAPPING.get(vtype, {})
    return Violation(
        violation_id=str(uuid.uuid4()),
        type=vtype,
        severity=severity,
        description=description,
        affected_accounts=affected,
        control_mapping={
            "control": mapping.get("control", ""),
            "control_id": mapping.get("control_id", ""),
            "d_statement": mapping.get("d_statement", ""),
        },
        remediation=remediation,
        found_at=datetime.now(timezone.utc).isoformat(),
    )


def detect_leavers_with_access(
    ad_users: list[ADUser], hr_employees: list[HREmployee]
) -> list[Violation]:
    """Join AD on HR by EmployeeID. Flag accounts where HR status is Leaver
    but the AD account is still enabled. Severity: CRITICAL."""
    hr_map = {e.EmployeeID: e for e in hr_employees}
    violations: list[Violation] = []

    for ad in ad_users:
        hr = hr_map.get(ad.EmployeeID)
        if hr is None:
            continue
        if hr.Status == "Leaver" and ad.Enabled:
            violations.append(_make_violation(
                vtype=ViolationType.LEAVER_ACTIVE,
                severity=Severity.CRITICAL,
                description=f"Leaver {ad.SamAccountName} (ID: {ad.EmployeeID}) "
                            f"still has an enabled AD account. "
                            f"Termination date: {hr.TerminationDate}",
                affected=[ad.SamAccountName],
                remediation="Disable AD account immediately. Revoke all group memberships. "
                            "Confirm access removal with application owners.",
            ))

    return violations


def detect_orphaned_accounts(
    ad_users: list[ADUser], hr_employees: list[HREmployee],
    staleness_days: int = 90
) -> list[Violation]:
    """Detect AD accounts with no matching HR record.
    Excludes service accounts (SVC_, APP_, SYS_ prefix).
    Also flags stale orphaned accounts (LastLogon > staleness_days).
    Severity: HIGH."""
    active_employees = {e.EmployeeID for e in hr_employees}
    violations: list[Violation] = []

    for ad in ad_users:
        if not ad.Enabled:
            continue
        if ad.is_service_account():
            continue
        if ad.EmployeeID not in active_employees:
            msg = f"Orphaned AD account {ad.SamAccountName} (ID: {ad.EmployeeID}) "
            msg += f"has no matching HR record."
            days = ad.days_since_logon()
            if days is not None and days > staleness_days:
                msg += f" Additionally stale ({days} days since last logon)."
        else:
            continue

        violations.append(_make_violation(
            vtype=ViolationType.ORPHANED,
            severity=Severity.HIGH,
            description=msg,
            affected=[ad.SamAccountName],
            remediation="Verify whether account is still needed. If not, disable "
                        "and schedule for deletion per offboarding policy. "
                        "If still required, update HR records.",
        ))

    return violations


def detect_missing_mfa(ad_users: list[ADUser]) -> list[Violation]:
    """Detect AD accounts where MFA is not enabled.
    Severity: HIGH for privileged accounts, MEDIUM for standard."""
    violations: list[Violation] = []

    for ad in ad_users:
        if not ad.Enabled:
            continue
        if ad.MFAEnabled:
            continue

        is_priv = ad.is_privileged()
        severity = Severity.HIGH if is_priv else Severity.MEDIUM
        desc = f"User {ad.SamAccountName} (ID: {ad.EmployeeID}) does not have MFA enabled. "
        if is_priv:
            desc += f"Account is a member of privileged group '{ad.Group}'."

        violations.append(_make_violation(
            vtype=ViolationType.MFA_MISSING,
            severity=severity,
            description=desc,
            affected=[ad.SamAccountName],
            remediation="Enforce MFA enrollment via conditional access policy. "
                        "For privileged accounts, require phishing-resistant MFA "
                        "(FIDO2 or similar).",
        ))

    return violations


def detect_self_approvals(itsm_tickets: list[ITSMTicket]) -> list[Violation]:
    """Detect ITSM tickets where RequestorID == ApproverID.
    This is a segregation of duties violation. Severity: HIGH."""
    violations: list[Violation] = []

    for ticket in itsm_tickets:
        if ticket.RequestorID == ticket.ApproverID:
            violations.append(_make_violation(
                vtype=ViolationType.SELF_APPROVAL,
                severity=Severity.HIGH,
                description=f"Ticket {ticket.TicketID}: Requestor {ticket.RequestorID} "
                            f"also acted as Approver for change type '{ticket.ChangeType}'. "
                            f"Created: {ticket.CreatedDate}",
                affected=[ticket.RequestorID],
                remediation="Require a separate approver for all access changes. "
                            "Implement dual-approval workflow in ITSM. "
                            "Review ticket for unauthorized access grants.",
            ))

    return violations


def run_all_checks(
    ad_users: list[ADUser],
    hr_employees: list[HREmployee],
    itsm_tickets: list[ITSMTicket],
) -> list[Violation]:
    """Orchestrator: run all detection checks and return combined violations."""
    violations: list[Violation] = []
    violations.extend(detect_leavers_with_access(ad_users, hr_employees))
    violations.extend(detect_orphaned_accounts(ad_users, hr_employees))
    violations.extend(detect_missing_mfa(ad_users))
    violations.extend(detect_self_approvals(itsm_tickets))
    return violations

"""Tests for the violation detection engine."""

from datetime import datetime, timezone, timedelta
from src.models import (
    ADUser, HREmployee, ITSMTicket, Severity, ViolationType,
)
from src.engine import (
    detect_leavers_with_access,
    detect_orphaned_accounts,
    detect_missing_mfa,
    detect_self_approvals,
    run_all_checks,
)


def _now():
    return datetime.now(timezone.utc)


class TestDetectLeaversWithAccess:
    def test_leaver_with_enabled_account_detected(self):
        ad = [ADUser(SamAccountName="leaver.one", EmployeeID="EMP001", Enabled=True)]
        hr = [HREmployee(EmployeeID="EMP001", Status="Leaver", TerminationDate=_now())]
        violations = detect_leavers_with_access(ad, hr)
        assert len(violations) == 1
        assert violations[0].type == ViolationType.LEAVER_ACTIVE
        assert violations[0].severity == Severity.CRITICAL
        assert "leaver.one" in violations[0].affected_accounts

    def test_leaver_with_disabled_account_not_flagged(self):
        ad = [ADUser(SamAccountName="leaver.done", EmployeeID="EMP001", Enabled=False)]
        hr = [HREmployee(EmployeeID="EMP001", Status="Leaver")]
        violations = detect_leavers_with_access(ad, hr)
        assert len(violations) == 0

    def test_active_employee_with_enabled_account_not_flagged(self):
        ad = [ADUser(SamAccountName="active.user", EmployeeID="EMP001", Enabled=True)]
        hr = [HREmployee(EmployeeID="EMP001", Status="Active")]
        violations = detect_leavers_with_access(ad, hr)
        assert len(violations) == 0

    def test_multiple_leavers_detected(self):
        ad = [
            ADUser(SamAccountName="leaver1", EmployeeID="E1", Enabled=True),
            ADUser(SamAccountName="leaver2", EmployeeID="E2", Enabled=True),
            ADUser(SamAccountName="active1", EmployeeID="E3", Enabled=True),
        ]
        hr = [
            HREmployee(EmployeeID="E1", Status="Leaver"),
            HREmployee(EmployeeID="E2", Status="Leaver"),
            HREmployee(EmployeeID="E3", Status="Active"),
        ]
        violations = detect_leavers_with_access(ad, hr)
        assert len(violations) == 2

    def test_ad_user_no_hr_record_not_flagged(self):
        ad = [ADUser(SamAccountName="ghost", EmployeeID="NO_MATCH", Enabled=True)]
        hr = [HREmployee(EmployeeID="E1", Status="Active")]
        violations = detect_leavers_with_access(ad, hr)
        assert len(violations) == 0


class TestDetectOrphanedAccounts:
    def test_orphaned_account_detected(self):
        ad = [ADUser(SamAccountName="orphan", EmployeeID="ORPH001", Enabled=True)]
        hr = [HREmployee(EmployeeID="E1", Status="Active")]
        violations = detect_orphaned_accounts(ad, hr)
        assert len(violations) == 1
        assert violations[0].type == ViolationType.ORPHANED
        assert violations[0].severity == Severity.HIGH

    def test_disabled_orphaned_not_flagged(self):
        ad = [ADUser(SamAccountName="orphan", EmployeeID="ORPH001", Enabled=False)]
        hr = []
        violations = detect_orphaned_accounts(ad, hr)
        assert len(violations) == 0

    def test_service_account_not_flagged_as_orphaned(self):
        ad = [
            ADUser(SamAccountName="SVC_mon", EmployeeID="SVC001", Enabled=True),
            ADUser(SamAccountName="APP_hr", EmployeeID="APP001", Enabled=True),
            ADUser(SamAccountName="SYS_bk", EmployeeID="SYS001", Enabled=True),
        ]
        hr = []
        violations = detect_orphaned_accounts(ad, hr)
        assert len(violations) == 0

    def test_active_employee_not_orphaned(self):
        ad = [ADUser(SamAccountName="active", EmployeeID="E1", Enabled=True)]
        hr = [HREmployee(EmployeeID="E1", Status="Active")]
        violations = detect_orphaned_accounts(ad, hr)
        assert len(violations) == 0

    def test_stale_orphan_has_staleness_in_description(self):
        old_date = _now() - timedelta(days=120)
        ad = [ADUser(SamAccountName="stale.orphan", EmployeeID="ORPH002",
                      Enabled=True, LastLogon=old_date)]
        hr = []
        violations = detect_orphaned_accounts(ad, hr)
        assert len(violations) == 1
        assert "stale" in violations[0].description.lower()


class TestDetectMissingMFA:
    def test_privileged_user_missing_mfa_is_high(self):
        ad = [ADUser(SamAccountName="admin", EmployeeID="E1",
                      Enabled=True, MFAEnabled=False, Group="Domain Admins")]
        violations = detect_missing_mfa(ad)
        assert len(violations) == 1
        assert violations[0].severity == Severity.HIGH
        assert violations[0].type == ViolationType.MFA_MISSING

    def test_standard_user_missing_mfa_is_medium(self):
        ad = [ADUser(SamAccountName="user", EmployeeID="E2",
                      Enabled=True, MFAEnabled=False, Group="Domain Users")]
        violations = detect_missing_mfa(ad)
        assert len(violations) == 1
        assert violations[0].severity == Severity.MEDIUM

    def test_user_with_mfa_not_flagged(self):
        ad = [ADUser(SamAccountName="user", EmployeeID="E1",
                      Enabled=True, MFAEnabled=True, Group="Domain Admins")]
        violations = detect_missing_mfa(ad)
        assert len(violations) == 0

    def test_disabled_user_not_flagged(self):
        ad = [ADUser(SamAccountName="disabled", EmployeeID="E1",
                      Enabled=False, MFAEnabled=False)]
        violations = detect_missing_mfa(ad)
        assert len(violations) == 0


class TestDetectSelfApprovals:
    def test_self_approval_detected(self):
        tickets = [ITSMTicket(TicketID="T1", RequestorID="EMP001",
                              ApproverID="EMP001", ChangeType="Access Request")]
        violations = detect_self_approvals(tickets)
        assert len(violations) == 1
        assert violations[0].type == ViolationType.SELF_APPROVAL
        assert violations[0].severity == Severity.HIGH

    def test_normal_ticket_not_flagged(self):
        tickets = [ITSMTicket(TicketID="T2", RequestorID="EMP001",
                              ApproverID="EMP008", ChangeType="Access Request")]
        violations = detect_self_approvals(tickets)
        assert len(violations) == 0

    def test_multiple_self_approvals_detected(self):
        tickets = [
            ITSMTicket(TicketID="T1", RequestorID="E1", ApproverID="E1"),
            ITSMTicket(TicketID="T2", RequestorID="E2", ApproverID="E3"),
            ITSMTicket(TicketID="T3", RequestorID="E3", ApproverID="E3"),
        ]
        violations = detect_self_approvals(tickets)
        assert len(violations) == 2


class TestRunAllChecks:
    def test_all_violations_returned(self):
        from src.data import load_sample_data
        ad, hr, itsm = load_sample_data()
        violations = run_all_checks(ad, hr, itsm)
        assert len(violations) > 0

    def test_clean_data_no_violations(self):
        ad = [ADUser(SamAccountName="clean", EmployeeID="E1", Enabled=True,
                      MFAEnabled=True, Group="Domain Users")]
        hr = [HREmployee(EmployeeID="E1", Status="Active")]
        itsm = [ITSMTicket(TicketID="T1", RequestorID="E1", ApproverID="E2")]
        violations = run_all_checks(ad, hr, itsm)
        assert len(violations) == 0

    def test_mixed_data_correct_counts(self):
        ad = [
            ADUser(SamAccountName="leaver.enabled", EmployeeID="E1", Enabled=True, MFAEnabled=True),
            ADUser(SamAccountName="orphan", EmployeeID="ORPH1", Enabled=True, MFAEnabled=True),
            ADUser(SamAccountName="admin.no.mfa", EmployeeID="E2", Enabled=True,
                   MFAEnabled=False, Group="Domain Admins"),
        ]
        hr = [
            HREmployee(EmployeeID="E1", Status="Leaver"),
            HREmployee(EmployeeID="E2", Status="Active"),
        ]
        itsm = [ITSMTicket(TicketID="T1", RequestorID="E1", ApproverID="E1")]
        violations = run_all_checks(ad, hr, itsm)
        # Should find: 1 leaver, 1 orphan, 1 missing MFA, 1 self-approval = 4
        assert len(violations) == 4
        types = {v.type for v in violations}
        assert len(types) == 4

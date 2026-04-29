"""Tests for domain models."""

from src.models import (
    ADUser, HREmployee, ITSMTicket, Violation,
    ViolationType, Severity, HRStatus, CONTROL_MAPPING,
    SEVERITY_SLA, PRIVILEGED_GROUPS,
)
from datetime import datetime, timezone


class TestADUser:
    def test_creation_defaults(self):
        u = ADUser(SamAccountName="test.user", EmployeeID="EMP001", Enabled=True)
        assert u.SamAccountName == "test.user"
        assert u.EmployeeID == "EMP001"
        assert u.Enabled is True
        assert u.MFAEnabled is False
        assert u.Group == "Domain Users"

    def test_is_privileged_true(self):
        for g in PRIVILEGED_GROUPS:
            u = ADUser(SamAccountName="admin", EmployeeID="ADM", Enabled=True, Group=g)
            assert u.is_privileged() is True

    def test_is_privileged_false(self):
        u = ADUser(SamAccountName="user", EmployeeID="EMP", Enabled=True, Group="Domain Users")
        assert u.is_privileged() is False

    def test_is_service_account(self):
        assert ADUser(SamAccountName="SVC_mon", EmployeeID="SVC001", Enabled=True).is_service_account() is True
        assert ADUser(SamAccountName="APP_hr", EmployeeID="APP001", Enabled=True).is_service_account() is True
        assert ADUser(SamAccountName="SYS_backup", EmployeeID="SYS001", Enabled=True).is_service_account() is True
        assert ADUser(SamAccountName="john.doe", EmployeeID="EMP001", Enabled=True).is_service_account() is False

    def test_days_since_logon(self):
        now = datetime.now(timezone.utc)
        from datetime import timedelta
        u = ADUser(SamAccountName="user", EmployeeID="E1", Enabled=True,
                   LastLogon=now - timedelta(days=30))
        assert u.days_since_logon() == 30

    def test_days_since_logon_none(self):
        u = ADUser(SamAccountName="user", EmployeeID="E1", Enabled=True)
        assert u.days_since_logon() is None


class TestHREmployee:
    def test_creation(self):
        e = HREmployee(EmployeeID="EMP001", Status="Active", Department="IT")
        assert e.EmployeeID == "EMP001"
        assert e.Status == "Active"
        assert e.Department == "IT"

    def test_leaver_with_termination_date(self):
        now = datetime.now(timezone.utc)
        e = HREmployee(EmployeeID="EMP002", Status="Leaver", TerminationDate=now)
        assert e.Status == "Leaver"
        assert e.TerminationDate == now


class TestITSMTicket:
    def test_creation(self):
        t = ITSMTicket(TicketID="ITSM-001", RequestorID="EMP001",
                       ApproverID="EMP008", ChangeType="Access Request")
        assert t.TicketID == "ITSM-001"
        assert t.RequestorID == "EMP001"
        assert t.ApproverID == "EMP008"


class TestViolation:
    def test_creation_and_to_dict(self):
        v = Violation(
            violation_id="v1",
            type=ViolationType.LEAVER_ACTIVE,
            severity=Severity.CRITICAL,
            description="Test leaver enabled",
            affected_accounts=["leaver.one"],
            remediation="Disable account",
        )
        d = v.to_dict()
        assert d["type"] == "LEAVER_ACTIVE"
        assert d["severity"] == "CRITICAL"
        assert d["violation_id"] == "v1"
        assert "leaver.one" in d["affected_accounts"]

    def test_to_dict_serializable(self):
        import json
        v = Violation(
            violation_id="v1",
            type=ViolationType.MFA_MISSING,
            severity=Severity.HIGH,
            description="No MFA",
            affected_accounts=["admin.jones"],
        )
        json.dumps(v.to_dict())


class TestControlMapping:
    def test_all_violation_types_mapped(self):
        for vt in ViolationType:
            assert vt in CONTROL_MAPPING, f"{vt} not in CONTROL_MAPPING"
            assert "control" in CONTROL_MAPPING[vt]
            assert "control_id" in CONTROL_MAPPING[vt]

    def test_leaver_active_mapping(self):
        m = CONTROL_MAPPING[ViolationType.LEAVER_ACTIVE]
        assert m["control_id"] == "IAC-01/D"

    def test_orphaned_mapping(self):
        m = CONTROL_MAPPING[ViolationType.ORPHANED]
        assert m["control_id"] == "IAC-02/D"

    def test_mfa_missing_mapping(self):
        m = CONTROL_MAPPING[ViolationType.MFA_MISSING]
        assert m["control_id"] == "IAC-03/D"

    def test_self_approval_mapping(self):
        m = CONTROL_MAPPING[ViolationType.SELF_APPROVAL]
        assert m["control_id"] == "IAC-04/D"


class TestSeveritySLA:
    def test_critical_24h(self):
        assert SEVERITY_SLA[Severity.CRITICAL]["hours"] == 24

    def test_high_7d(self):
        assert SEVERITY_SLA[Severity.HIGH]["days"] == 7

    def test_medium_30d(self):
        assert SEVERITY_SLA[Severity.MEDIUM]["days"] == 30

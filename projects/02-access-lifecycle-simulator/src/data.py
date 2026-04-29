"""Built-in sample data generator for demo mode.

Generates ~15 AD users, ~15 HR employees, ~10 ITSM tickets.
Seeds known violations of each type so the demo always produces findings.
"""

from datetime import datetime, timezone, timedelta
from .models import ADUser, HREmployee, ITSMTicket


def generate_ad_users() -> list[ADUser]:
    now = datetime.now(timezone.utc)
    return [
        # Regular active users
        ADUser(SamAccountName="john.smith", EmployeeID="EMP001", Enabled=True,
               LastLogon=now - timedelta(hours=2), MFAEnabled=True, Group="Domain Users"),
        ADUser(SamAccountName="jane.doe", EmployeeID="EMP002", Enabled=True,
               LastLogon=now - timedelta(days=1), MFAEnabled=True, Group="Domain Users"),
        ADUser(SamAccountName="bob.wilson", EmployeeID="EMP003", Enabled=True,
               LastLogon=now - timedelta(days=5), MFAEnabled=False, Group="Domain Users"),
        ADUser(SamAccountName="alice.jones", EmployeeID="EMP004", Enabled=True,
               LastLogon=now - timedelta(days=3), MFAEnabled=True, Group="Domain Users"),

        # LEAVER -- account still enabled (CRITICAL violation)
        ADUser(SamAccountName="leaver.one", EmployeeID="EMP005", Enabled=True,
               LastLogon=now - timedelta(days=45), MFAEnabled=True, Group="Domain Users"),
        ADUser(SamAccountName="leaver.two", EmployeeID="EMP006", Enabled=True,
               LastLogon=now - timedelta(days=60), MFAEnabled=False, Group="Domain Users"),

        # LEAVER -- properly disabled (no violation)
        ADUser(SamAccountName="leaver.disabled", EmployeeID="EMP007", Enabled=False,
               LastLogon=now - timedelta(days=90), MFAEnabled=False, Group="Domain Users"),

        # Orphaned -- AD account with no HR record (HIGH violation)
        ADUser(SamAccountName="orphan.user1", EmployeeID="ORPH001", Enabled=True,
               LastLogon=now - timedelta(days=10), MFAEnabled=True, Group="Domain Users"),
        ADUser(SamAccountName="orphan.user2", EmployeeID="ORPH002", Enabled=True,
               LastLogon=now - timedelta(days=120), MFAEnabled=False, Group="Domain Users"),

        # Service accounts -- should be excluded from orphan detection
        ADUser(SamAccountName="SVC_Monitoring", EmployeeID="SVC001", Enabled=True,
               LastLogon=now - timedelta(hours=1), MFAEnabled=False, Group="Service Accounts"),
        ADUser(SamAccountName="APP_HRConnector", EmployeeID="APP001", Enabled=True,
               LastLogon=now - timedelta(minutes=30), MFAEnabled=False, Group="Service Accounts"),

        # Privileged users -- one with MFA, one without (HIGH violation)
        ADUser(SamAccountName="admin.smith", EmployeeID="EMP008", Enabled=True,
               LastLogon=now - timedelta(hours=4), MFAEnabled=True, Group="Domain Admins"),
        ADUser(SamAccountName="admin.jones", EmployeeID="EMP009", Enabled=True,
               LastLogon=now - timedelta(hours=6), MFAEnabled=False, Group="Domain Admins"),
        ADUser(SamAccountName="server.op", EmployeeID="EMP010", Enabled=True,
               LastLogon=now - timedelta(days=2), MFAEnabled=False, Group="Server Operators"),

        # User on leave -- HR shows Active, AD enabled, short-term non-issue
        ADUser(SamAccountName="on.leave", EmployeeID="EMP011", Enabled=True,
               LastLogon=now - timedelta(days=14), MFAEnabled=True, Group="Domain Users"),
    ]


def generate_hr_employees() -> list[HREmployee]:
    now = datetime.now(timezone.utc)
    return [
        # Active employees
        HREmployee(EmployeeID="EMP001", Status="Active", Department="Engineering"),
        HREmployee(EmployeeID="EMP002", Status="Active", Department="Finance"),
        HREmployee(EmployeeID="EMP003", Status="Active", Department="Engineering"),
        HREmployee(EmployeeID="EMP004", Status="Active", Department="Legal"),
        HREmployee(EmployeeID="EMP005", Status="Leaver", Department="Sales",
                   TerminationDate=now - timedelta(days=30)),
        HREmployee(EmployeeID="EMP006", Status="Leaver", Department="Marketing",
                   TerminationDate=now - timedelta(days=60)),
        HREmployee(EmployeeID="EMP007", Status="Leaver", Department="IT",
                   TerminationDate=now - timedelta(days=90)),
        HREmployee(EmployeeID="EMP008", Status="Active", Department="IT"),
        HREmployee(EmployeeID="EMP009", Status="Active", Department="IT"),
        HREmployee(EmployeeID="EMP010", Status="Active", Department="IT"),
        HREmployee(EmployeeID="EMP011", Status="Active", Department="HR"),
        # Active employees with no matching AD account (gap, but not orphan detection scope)
        HREmployee(EmployeeID="EMP012", Status="Active", Department="Sales"),
        HREmployee(EmployeeID="EMP013", Status="Active", Department="Marketing"),
        # On-leave employee
        HREmployee(EmployeeID="EMP014", Status="On-Leave", Department="Finance"),
        # Mover
        HREmployee(EmployeeID="EMP015", Status="Mover", Department="Engineering"),
    ]


def generate_itsm_tickets() -> list[ITSMTicket]:
    now = datetime.now(timezone.utc)
    return [
        # Normal tickets -- requester != approver
        ITSMTicket(TicketID="ITSM-001", RequestorID="EMP001", ApproverID="EMP008",
                   ChangeType="Access Request", CreatedDate=now - timedelta(days=5)),
        ITSMTicket(TicketID="ITSM-002", RequestorID="EMP003", ApproverID="EMP008",
                   ChangeType="Access Request", CreatedDate=now - timedelta(days=3)),
        ITSMTicket(TicketID="ITSM-003", RequestorID="EMP002", ApproverID="EMP009",
                   ChangeType="Privilege Escalation", CreatedDate=now - timedelta(days=7)),
        ITSMTicket(TicketID="ITSM-004", RequestorID="EMP004", ApproverID="EMP008",
                   ChangeType="Access Request", CreatedDate=now - timedelta(days=2)),
        # Self-approval tickets (HIGH violation)
        ITSMTicket(TicketID="ITSM-005", RequestorID="EMP008", ApproverID="EMP008",
                   ChangeType="Privilege Escalation", CreatedDate=now - timedelta(days=1)),
        ITSMTicket(TicketID="ITSM-006", RequestorID="EMP009", ApproverID="EMP009",
                   ChangeType="Access Request", CreatedDate=now - timedelta(days=4)),
        # Normal tickets
        ITSMTicket(TicketID="ITSM-007", RequestorID="EMP005", ApproverID="EMP008",
                   ChangeType="Access Removal", CreatedDate=now - timedelta(days=30)),
        ITSMTicket(TicketID="ITSM-008", RequestorID="EMP001", ApproverID="EMP009",
                   ChangeType="Access Request", CreatedDate=now - timedelta(days=6)),
        # More normal tickets
        ITSMTicket(TicketID="ITSM-009", RequestorID="EMP011", ApproverID="EMP008",
                   ChangeType="Access Request", CreatedDate=now - timedelta(days=8)),
        ITSMTicket(TicketID="ITSM-010", RequestorID="EMP003", ApproverID="EMP009",
                   ChangeType="Access Removal", CreatedDate=now - timedelta(days=10)),
    ]


def load_sample_data():
    """Load all sample datasets in one call. Returns tuple of (ad, hr, itsm)."""
    return generate_ad_users(), generate_hr_employees(), generate_itsm_tickets()

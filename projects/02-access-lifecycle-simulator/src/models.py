"""Domain models for IAM Access Lifecycle Simulator."""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class HRStatus(str, Enum):
    ACTIVE = "Active"
    LEAVER = "Leaver"
    MOVER = "Mover"
    ON_LEAVE = "On-Leave"


class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"


class ViolationType(str, Enum):
    LEAVER_ACTIVE = "LEAVER_ACTIVE"
    ORPHANED = "ORPHANED"
    MFA_MISSING = "MFA_MISSING"
    SELF_APPROVAL = "SELF_APPROVAL"


CONTROL_MAPPING = {
    ViolationType.LEAVER_ACTIVE: {
        "control": "Removal of access rights for leavers",
        "control_id": "IAC-01/D",
        "d_statement": "D1,D3,D5",
    },
    ViolationType.ORPHANED: {
        "control": "User registration and de-registration",
        "control_id": "IAC-02/D",
        "d_statement": "D4,D5",
    },
    ViolationType.MFA_MISSING: {
        "control": "Multi-factor authentication",
        "control_id": "IAC-03/D",
        "d_statement": "D2,D3",
    },
    ViolationType.SELF_APPROVAL: {
        "control": "User access provisioning",
        "control_id": "IAC-04/D",
        "d_statement": "D3,D4",
    },
}

SEVERITY_SLA = {
    Severity.CRITICAL: {"hours": 24},
    Severity.HIGH: {"days": 7},
    Severity.MEDIUM: {"days": 30},
}

PRIVILEGED_GROUPS = {
    "Domain Admins",
    "Enterprise Admins",
    "Schema Admins",
    "Administrators",
    "Server Operators",
    "Account Operators",
    "Backup Operators",
}


@dataclass
class ADUser:
    SamAccountName: str
    EmployeeID: str
    Enabled: bool
    LastLogon: Optional[datetime] = None
    MFAEnabled: bool = False
    Group: str = "Domain Users"
    ManagerDN: str = ""

    def days_since_logon(self) -> Optional[int]:
        if self.LastLogon is None:
            return None
        return (datetime.now(timezone.utc) - self.LastLogon).days

    def is_privileged(self) -> bool:
        g = self.Group or ""
        return g in PRIVILEGED_GROUPS

    def is_service_account(self) -> bool:
        return self.SamAccountName.startswith(("SVC_", "APP_", "SYS_"))


@dataclass
class HREmployee:
    EmployeeID: str
    Status: str
    Department: str = ""
    ManagerID: str = ""
    TerminationDate: Optional[datetime] = None


@dataclass
class ITSMTicket:
    TicketID: str
    RequestorID: str
    ApproverID: str
    ChangeType: str = "Access Request"
    CreatedDate: Optional[datetime] = None


@dataclass
class Violation:
    violation_id: str
    type: ViolationType
    severity: Severity
    description: str
    affected_accounts: list[str] = field(default_factory=list)
    control_mapping: dict = field(default_factory=dict)
    remediation: str = ""
    found_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        d = asdict(self)
        d["type"] = self.type.value
        d["severity"] = self.severity.value
        return d


@dataclass
class AuditReport:
    audit_date: str
    scope: str
    summary: dict
    violations: list[Violation] = field(default_factory=list)
    access_certification_items: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["violations"] = [v.to_dict() for v in self.violations]
        return d

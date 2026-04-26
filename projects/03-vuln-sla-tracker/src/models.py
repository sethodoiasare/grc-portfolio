"""
Domain models for the Vuln SLA Tracker.

Vulnerabilities, scanner runs, SLA rules, breaches, and KPI aggregates.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class Severity(str, Enum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    INFO = "Info"


class VulnStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"
    RISK_ACCEPTED = "risk_accepted"
    FALSE_POSITIVE = "false_positive"


class ScannerType(str, Enum):
    NESSUS = "nessus"
    OPENVAS = "openvas"
    QUALYS = "qualys"


# SLA remediation windows in days, per severity
SLA_DEADLINES = {
    Severity.CRITICAL: 7,
    Severity.HIGH: 30,
    Severity.MEDIUM: 90,
    Severity.LOW: 180,
    Severity.INFO: 365,
}


def severity_from_cvss(cvss: float) -> Severity:
    if cvss >= 9.0:
        return Severity.CRITICAL
    if cvss >= 7.0:
        return Severity.HIGH
    if cvss >= 4.0:
        return Severity.MEDIUM
    if cvss > 0:
        return Severity.LOW
    return Severity.INFO


def sla_deadline_days(severity: Severity) -> int:
    return SLA_DEADLINES.get(severity, 180)


@dataclass
class Vulnerability:
    """A single vulnerability finding from a scanner."""
    id: Optional[int] = None
    scanner_run_id: Optional[int] = None
    scanner_type: str = ""
    asset_hostname: str = ""
    asset_ip: str = ""
    title: str = ""
    description: str = ""
    severity: str = ""
    cvss_score: float = 0.0
    cve_id: str = ""
    port: Optional[int] = None
    protocol: str = ""
    solution: str = ""
    status: str = VulnStatus.OPEN.value
    first_seen: Optional[str] = None
    last_seen: Optional[str] = None
    closed_at: Optional[str] = None
    risk_accepted_at: Optional[str] = None
    days_open: int = 0
    sla_deadline_days: int = 0
    sla_breach_days: int = 0

    def to_dict(self) -> dict:
        return {
            "id": self.id, "scanner_run_id": self.scanner_run_id,
            "scanner_type": self.scanner_type, "asset_hostname": self.asset_hostname,
            "asset_ip": self.asset_ip, "title": self.title,
            "description": self.description, "severity": self.severity,
            "cvss_score": self.cvss_score, "cve_id": self.cve_id,
            "port": self.port, "protocol": self.protocol,
            "solution": self.solution, "status": self.status,
            "first_seen": self.first_seen, "last_seen": self.last_seen,
            "closed_at": self.closed_at, "risk_accepted_at": self.risk_accepted_at,
            "days_open": self.days_open, "sla_deadline_days": self.sla_deadline_days,
            "sla_breach_days": self.sla_breach_days,
        }


@dataclass
class ScannerRun:
    """A single scanner export ingestion run."""
    id: Optional[int] = None
    scanner_type: str = ""
    filename: str = ""
    vulns_imported: int = 0
    vulns_new: int = 0
    vulns_updated: int = 0
    imported_at: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id, "scanner_type": self.scanner_type,
            "filename": self.filename, "vulns_imported": self.vulns_imported,
            "vulns_new": self.vulns_new, "vulns_updated": self.vulns_updated,
            "imported_at": self.imported_at,
        }


@dataclass
class SLAKPI:
    """Aggregated KPI snapshot."""
    total_open: int = 0
    total_closed: int = 0
    total_risk_accepted: int = 0
    breached_count: int = 0
    breach_rate_pct: float = 0.0
    mttr_days: Optional[float] = None
    critical_open: int = 0
    high_open: int = 0
    medium_open: int = 0
    low_open: int = 0
    avg_cvss: float = 0.0

    def to_dict(self) -> dict:
        return {
            "total_open": self.total_open,
            "total_closed": self.total_closed,
            "total_risk_accepted": self.total_risk_accepted,
            "breached_count": self.breached_count,
            "breach_rate_pct": round(self.breach_rate_pct, 1),
            "mttr_days": round(self.mttr_days, 1) if self.mttr_days else None,
            "critical_open": self.critical_open,
            "high_open": self.high_open,
            "medium_open": self.medium_open,
            "low_open": self.low_open,
            "avg_cvss": round(self.avg_cvss, 1),
        }

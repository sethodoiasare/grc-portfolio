"""Domain models for Security Metrics Pack."""

from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime, timezone
from typing import Optional


class MetricSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class SLABreach(str, Enum):
    WITHIN_SLA = "WITHIN_SLA"
    BREACHED = "BREACHED"
    CRITICAL_BREACH = "CRITICAL_BREACH"


@dataclass
class IncidentRecord:
    """A single security incident for MTTD/MTTR calculation."""
    incident_id: str
    detected_at: str  # ISO datetime
    responded_at: Optional[str] = None  # ISO datetime, None if still open
    resolved_at: Optional[str] = None
    severity: MetricSeverity = MetricSeverity.MEDIUM
    source: str = ""


@dataclass
class AlertRecord:
    """A single security alert for quality metrics."""
    alert_id: str
    timestamp: str
    is_true_positive: bool
    is_false_positive: bool
    severity: MetricSeverity = MetricSeverity.MEDIUM
    source: str = ""
    category: str = ""


@dataclass
class VulnerabilityRecord:
    """A vulnerability finding for SLA tracking."""
    vuln_id: str
    discovered_at: str
    severity: MetricSeverity
    cvss_score: float
    fixed_at: Optional[str] = None
    sla_days: int = 30  # days allowed before SLA breach
    affected_system: str = ""


@dataclass
class MTTDMTTR:
    """Mean Time to Detect / Mean Time to Respond / Mean Time to Resolve."""
    mttd_hours: float
    mttr_hours: float  # respond
    mtt_resolve_hours: float
    total_incidents: int
    open_incidents: int
    avg_by_severity: dict[str, dict] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class AlertQuality:
    """Alert quality metrics."""
    total_alerts: int
    true_positives: int
    false_positives: int
    precision_pct: float
    false_positive_rate_pct: float
    by_source: dict[str, dict] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class VulnSLA:
    """Vulnerability SLA compliance metrics."""
    total_vulnerabilities: int
    within_sla: int
    breached: int
    critical_breached: int
    sla_compliance_pct: float
    mttr_vuln_hours: float
    overdue_critical: int
    by_severity: dict[str, dict] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class TrendPoint:
    """A single data point in a trend series."""
    date: str
    value: float
    label: str = ""


@dataclass
class MetricReport:
    """Complete security metrics report."""
    report_id: str
    generated_at: str
    period_start: str
    period_end: str
    mttd_mttr: MTTDMTTR
    alert_quality: AlertQuality
    vuln_sla: VulnSLA
    trends: dict[str, list[TrendPoint]] = field(default_factory=dict)

    def rag_status(self) -> str:
        scores = []
        if self.mttd_mttr.mttd_hours > 24:
            scores.append("RED")
        elif self.mttd_mttr.mttd_hours > 8:
            scores.append("AMBER")
        if self.alert_quality.false_positive_rate_pct > 20:
            scores.append("RED")
        elif self.alert_quality.false_positive_rate_pct > 10:
            scores.append("AMBER")
        if self.vuln_sla.sla_compliance_pct < 70:
            scores.append("RED")
        elif self.vuln_sla.sla_compliance_pct < 85:
            scores.append("AMBER")
        if "RED" in scores:
            return "RED"
        if "AMBER" in scores:
            return "AMBER"
        return "GREEN"

    def to_dict(self) -> dict:
        return {
            "report_id": self.report_id,
            "generated_at": self.generated_at,
            "period_start": self.period_start,
            "period_end": self.period_end,
            "rag_status": self.rag_status(),
            "mttd_mttr": self.mttd_mttr.to_dict(),
            "alert_quality": self.alert_quality.to_dict(),
            "vuln_sla": self.vuln_sla.to_dict(),
            "trends": {k: [asdict(t) for t in v] for k, v in self.trends.items()},
        }

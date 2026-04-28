"""Orchestration: compute all metrics from input data."""

import uuid
from datetime import datetime, timezone

from .models import (
    IncidentRecord, AlertRecord, VulnerabilityRecord,
    MTTDMTTR, AlertQuality, VulnSLA, MetricReport,
)
from .metrics import compute_mttd_mttr, compute_alert_quality, compute_vuln_sla


def compute(
    incidents: list[IncidentRecord] | None = None,
    alerts: list[AlertRecord] | None = None,
    vulns: list[VulnerabilityRecord] | None = None,
    period_start: str = "",
    period_end: str = "",
) -> MetricReport:
    """Compute all security metrics from provided records."""
    incidents = incidents or []
    alerts = alerts or []
    vulns = vulns or []

    mttd_mttr = compute_mttd_mttr(incidents)
    alert_quality = compute_alert_quality(alerts)
    vuln_sla = compute_vuln_sla(vulns)

    return MetricReport(
        report_id=str(uuid.uuid4()),
        generated_at=datetime.now(timezone.utc).isoformat(),
        period_start=period_start or "N/A",
        period_end=period_end or "N/A",
        mttd_mttr=mttd_mttr,
        alert_quality=alert_quality,
        vuln_sla=vuln_sla,
    )

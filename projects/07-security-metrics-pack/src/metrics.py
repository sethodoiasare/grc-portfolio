"""Metrics computation engine: MTTD, MTTR, alert quality, vuln SLA."""

from datetime import datetime, timezone
from collections import defaultdict

from .models import (
    IncidentRecord, AlertRecord, VulnerabilityRecord,
    MTTDMTTR, AlertQuality, VulnSLA, MetricSeverity,
)


def compute_mttd_mttr(incidents: list[IncidentRecord]) -> MTTDMTTR:
    """Calculate MTTD, MTTR (respond), and MTTR (resolve) from incident records."""
    if not incidents:
        return MTTDMTTR(mttd_hours=0, mttr_hours=0, mtt_resolve_hours=0,
                        total_incidents=0, open_incidents=0)

    ttd_values = []
    ttr_values = []
    ttr_resolve_values = []
    by_severity: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))

    for inc in incidents:
        detected = datetime.fromisoformat(inc.detected_at)

        # MTTD: for demo, detection is the incident creation (time from detection = 0)
        # In practice this would be time from event occurrence to detection
        ttd_values.append(0)

        if inc.responded_at:
            responded = datetime.fromisoformat(inc.responded_at)
            ttr_h = (responded - detected).total_seconds() / 3600
            ttr_values.append(ttr_h)
            by_severity[inc.severity.value]["respond_hours"] = \
                by_severity[inc.severity.value].get("respond_hours", []) + [ttr_h]

        if inc.resolved_at:
            resolved = datetime.fromisoformat(inc.resolved_at)
            resolve_h = (resolved - detected).total_seconds() / 3600
            ttr_resolve_values.append(resolve_h)
            by_severity[inc.severity.value]["resolve_hours"] = \
                by_severity[inc.severity.value].get("resolve_hours", []) + [resolve_h]

    open_count = sum(1 for i in incidents if i.resolved_at is None)

    def _avg(vals):
        return round(sum(vals) / len(vals), 1) if vals else 0.0

    avg_by_sev = {}
    for sev, metrics in by_severity.items():
        avg_by_sev[sev] = {
            "avg_respond_hours": _avg(metrics.get("respond_hours", [])),
            "avg_resolve_hours": _avg(metrics.get("resolve_hours", [])),
            "count": sum(1 for i in incidents if i.severity.value == sev),
        }

    return MTTDMTTR(
        mttd_hours=_avg(ttd_values),
        mttr_hours=_avg(ttr_values),
        mtt_resolve_hours=_avg(ttr_resolve_values),
        total_incidents=len(incidents),
        open_incidents=open_count,
        avg_by_severity=avg_by_sev,
    )


def compute_alert_quality(alerts: list[AlertRecord]) -> AlertQuality:
    """Calculate alert precision and false positive rate."""
    if not alerts:
        return AlertQuality(total_alerts=0, true_positives=0, false_positives=0,
                           precision_pct=0.0, false_positive_rate_pct=0.0)

    tp = sum(1 for a in alerts if a.is_true_positive)
    fp = sum(1 for a in alerts if a.is_false_positive)
    total = len(alerts)

    precision = round(tp / total * 100, 1) if total > 0 else 0.0
    fpr = round(fp / total * 100, 1) if total > 0 else 0.0

    by_source: dict[str, dict] = defaultdict(lambda: {"total": 0, "tp": 0, "fp": 0})
    for a in alerts:
        by_source[a.source]["total"] += 1
        if a.is_true_positive:
            by_source[a.source]["tp"] += 1
        if a.is_false_positive:
            by_source[a.source]["fp"] += 1
    for src, data in by_source.items():
        data["precision_pct"] = round(data["tp"] / data["total"] * 100, 1) if data["total"] > 0 else 0.0

    return AlertQuality(
        total_alerts=total,
        true_positives=tp,
        false_positives=fp,
        precision_pct=precision,
        false_positive_rate_pct=fpr,
        by_source=dict(by_source),
    )


def compute_vuln_sla(vulns: list[VulnerabilityRecord]) -> VulnSLA:
    """Calculate vulnerability SLA compliance: breach rate, MTTR, overdue criticals."""
    if not vulns:
        return VulnSLA(total_vulnerabilities=0, within_sla=0, breached=0,
                      critical_breached=0, sla_compliance_pct=100.0,
                      mttr_vuln_hours=0.0, overdue_critical=0)

    within = 0
    breached = 0
    critical_breached = 0
    fix_times: list[float] = []
    by_severity: dict[str, dict] = defaultdict(lambda: {"total": 0, "breached": 0, "fixed": 0, "fix_times": []})

    for v in vulns:
        discovered = datetime.fromisoformat(v.discovered_at)
        sev = v.severity.value
        by_severity[sev]["total"] += 1

        if v.fixed_at:
            fixed = datetime.fromisoformat(v.fixed_at)
            hours = (fixed - discovered).total_seconds() / 3600
            days = hours / 24
            fix_times.append(hours)
            by_severity[sev]["fixed"] += 1
            by_severity[sev]["fix_times"].append(hours)

            if days <= v.sla_days:
                within += 1
            else:
                breached += 1
                by_severity[sev]["breached"] += 1
                if v.severity == MetricSeverity.CRITICAL:
                    critical_breached += 1
        else:
            breached += 1
            by_severity[sev]["breached"] += 1
            if v.severity == MetricSeverity.CRITICAL:
                critical_breached += 1

    total = len(vulns)
    compliance = round(within / total * 100, 1) if total > 0 else 100.0
    mttr_v = round(sum(fix_times) / len(fix_times), 1) if fix_times else 0.0
    overdue_crit = sum(1 for v in vulns
                       if v.severity == MetricSeverity.CRITICAL and v.fixed_at is None)

    sev_summary = {}
    for sev, data in by_severity.items():
        sev_summary[sev] = {
            "total": data["total"],
            "breached": data["breached"],
            "compliance_pct": round((data["total"] - data["breached"]) / data["total"] * 100, 1)
                              if data["total"] > 0 else 100.0,
            "avg_fix_hours": round(sum(data["fix_times"]) / len(data["fix_times"]), 1)
                            if data["fix_times"] else 0.0,
        }

    return VulnSLA(
        total_vulnerabilities=total,
        within_sla=within,
        breached=breached,
        critical_breached=critical_breached,
        sla_compliance_pct=compliance,
        mttr_vuln_hours=mttr_v,
        overdue_critical=overdue_crit,
        by_severity=sev_summary,
    )

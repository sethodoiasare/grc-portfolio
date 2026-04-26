"""
SLA calculation engine.

Computes days_open, sla_breach_days per vulnerability, and aggregated KPIs.
"""

from datetime import datetime, timedelta
from typing import Optional

from src.models import (
    Severity, VulnStatus, SLA_DEADLINES, SLAKPI, sla_deadline_days, severity_from_cvss,
)
from src.database import get_db, rows_to_list


def compute_vuln_sla(vuln: dict, as_of: Optional[datetime] = None) -> dict:
    """Enrich a vulnerability row with SLA fields: days_open, sla_deadline_days, sla_breach_days."""
    if as_of is None:
        as_of = datetime.utcnow()

    severity = Severity(vuln["severity"]) if vuln["severity"] in [s.value for s in Severity] else Severity.MEDIUM
    deadline = sla_deadline_days(severity)

    first_seen_str = vuln.get("first_seen", "")
    if first_seen_str:
        first_seen = datetime.fromisoformat(first_seen_str.replace("Z", ""))
        days_open = (as_of - first_seen).days
    else:
        days_open = 0

    status = vuln.get("status", "open")
    breach_days = 0
    if status == VulnStatus.OPEN.value and days_open > deadline:
        breach_days = days_open - deadline
    elif status == VulnStatus.CLOSED.value:
        first = datetime.fromisoformat(first_seen_str.replace("Z", "")) if first_seen_str else as_of
        closed_str = vuln.get("closed_at", "")
        closed = datetime.fromisoformat(closed_str.replace("Z", "")) if closed_str else as_of
        actual_remediation = (closed - first).days
        if actual_remediation > deadline:
            breach_days = actual_remediation - deadline
            days_open = actual_remediation
        else:
            breach_days = 0
            days_open = actual_remediation

    return {**vuln, "days_open": days_open, "sla_deadline_days": deadline, "sla_breach_days": max(0, breach_days)}


def compute_kpis() -> SLAKPI:
    """Compute SLA KPIs across all vulnerabilities."""
    conn = get_db()
    try:
        total = conn.execute("SELECT COUNT(*) FROM vulnerabilities").fetchone()[0]
        if total == 0:
            return SLAKPI()

        statuses = conn.execute(
            "SELECT status, COUNT(*) as cnt FROM vulnerabilities GROUP BY status"
        ).fetchall()
        status_map = {r["status"]: r["cnt"] for r in statuses}

        kpi = SLAKPI(
            total_open=status_map.get("open", 0),
            total_closed=status_map.get("closed", 0),
            total_risk_accepted=status_map.get("risk_accepted", 0),
        )

        sevs = conn.execute(
            "SELECT severity, COUNT(*) as cnt FROM vulnerabilities WHERE status = 'open' GROUP BY severity"
        ).fetchall()
        for r in sevs:
            if r["severity"] == Severity.CRITICAL.value:
                kpi.critical_open = r["cnt"]
            elif r["severity"] == Severity.HIGH.value:
                kpi.high_open = r["cnt"]
            elif r["severity"] == Severity.MEDIUM.value:
                kpi.medium_open = r["cnt"]
            elif r["severity"] == Severity.LOW.value:
                kpi.low_open = r["cnt"]

        avg_cvss_row = conn.execute(
            "SELECT AVG(cvss_score) as avg_cvss FROM vulnerabilities WHERE status = 'open'"
        ).fetchone()
        kpi.avg_cvss = round(avg_cvss_row["avg_cvss"], 1) if avg_cvss_row["avg_cvss"] else 0.0

        # Breach count: open vulns past their SLA deadline
        now = datetime.utcnow()
        breached = 0
        open_vulns = conn.execute(
            "SELECT severity, first_seen FROM vulnerabilities WHERE status = 'open'"
        ).fetchall()
        for v in open_vulns:
            if v["first_seen"]:
                first = datetime.fromisoformat(v["first_seen"].replace("Z", ""))
                days_open = (now - first).days
                deadline = sla_deadline_days(Severity(v["severity"]) if v["severity"] in [s.value for s in Severity] else Severity.MEDIUM)
                if days_open > deadline:
                    breached += 1
        kpi.breached_count = breached
        kpi.breach_rate_pct = round((breached / kpi.total_open * 100), 1) if kpi.total_open > 0 else 0.0

        # MTTR from closed vulns
        mttr_row = conn.execute(
            "SELECT first_seen, closed_at FROM vulnerabilities WHERE status = 'closed' AND closed_at IS NOT NULL"
        ).fetchall()
        if mttr_row:
            ttrs = []
            for r in mttr_row:
                try:
                    f = datetime.fromisoformat(r["first_seen"].replace("Z", ""))
                    c = datetime.fromisoformat(r["closed_at"].replace("Z", ""))
                    ttrs.append((c - f).days)
                except (ValueError, AttributeError):
                    pass
            kpi.mttr_days = round(sum(ttrs) / len(ttrs), 1) if ttrs else None

        return kpi
    finally:
        conn.close()


def get_top_overdue(limit: int = 10) -> list[dict]:
    """Return the top N most overdue open vulnerabilities."""
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT * FROM vulnerabilities WHERE status = 'open' AND first_seen IS NOT NULL ORDER BY first_seen ASC LIMIT ?",
            (limit,),
        ).fetchall()
        results = []
        for r in rows_to_list(rows):
            enriched = compute_vuln_sla(r)
            results.append(enriched)
        results.sort(key=lambda v: v["sla_breach_days"], reverse=True)
        return results
    finally:
        conn.close()


def get_breach_timeline(days: int = 90) -> list[dict]:
    """Return daily breach counts for the past N days (trend data)."""
    conn = get_db()
    try:
        timeline = []
        now = datetime.utcnow()
        for i in range(days, -1, -1):
            date = now - timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")
            count = conn.execute(
                """SELECT COUNT(*) FROM vulnerabilities
                   WHERE status IN ('open', 'closed')
                     AND first_seen <= ?
                     AND (closed_at IS NULL OR closed_at >= ?)""",
                (date_str, date_str),
            ).fetchone()[0]

            breached = conn.execute(
                """SELECT COUNT(*) FROM vulnerabilities v
                   WHERE status = 'open' AND first_seen <= ?""",
                (date_str,),
            ).fetchone()[0]

            timeline.append({"date": date_str, "total_open": count, "breached": breached})
        return timeline
    finally:
        conn.close()

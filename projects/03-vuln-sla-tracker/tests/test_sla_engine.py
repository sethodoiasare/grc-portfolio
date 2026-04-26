"""Tests for SLA engine computation and KPI aggregation."""

import pytest
from datetime import datetime, timedelta
from src.sla_engine import compute_vuln_sla, compute_kpis
from src.database import init_db, get_db


@pytest.fixture(autouse=True)
def _setup_db():
    """Reset the database before each test."""
    import os
    db_path = os.path.join(os.path.dirname(__file__), "..", "data", "vuln_sla_test.db")
    if os.path.exists(db_path):
        os.remove(db_path)
    os.environ["DATABASE_PATH"] = db_path
    init_db()
    yield
    if os.path.exists(db_path):
        os.remove(db_path)
    os.environ.pop("DATABASE_PATH", None)


def test_compute_vuln_sla_open_breached():
    """An open vulnerability past its SLA deadline should have breach days."""
    first = (datetime.utcnow() - timedelta(days=20))
    vuln = {
        "id": 1, "severity": "High", "status": "open",
        "first_seen": first.isoformat() + "Z",
    }
    result = compute_vuln_sla(vuln)
    assert result["days_open"] == 20
    assert result["sla_deadline_days"] == 30
    assert result["sla_breach_days"] == 0  # Not breached yet (High = 30 days)


def test_compute_vuln_sla_critical_breached():
    """A critical vulnerability open past 7 days is breached."""
    first = (datetime.utcnow() - timedelta(days=15))
    vuln = {
        "id": 1, "severity": "Critical", "status": "open",
        "first_seen": first.isoformat() + "Z",
    }
    result = compute_vuln_sla(vuln)
    assert result["days_open"] == 15
    assert result["sla_deadline_days"] == 7
    assert result["sla_breach_days"] == 8


def test_compute_vuln_sla_open_compliant():
    """An open vulnerability within SLA window should have zero breach days."""
    first = (datetime.utcnow() - timedelta(days=3))
    vuln = {
        "id": 2, "severity": "Medium", "status": "open",
        "first_seen": first.isoformat() + "Z",
    }
    result = compute_vuln_sla(vuln)
    assert result["days_open"] == 3
    assert result["sla_deadline_days"] == 90
    assert result["sla_breach_days"] == 0


def test_compute_vuln_sla_closed():
    """A closed vulnerability retains its resolution time."""
    first = (datetime.utcnow() - timedelta(days=40))
    closed = (datetime.utcnow() - timedelta(days=5))
    vuln = {
        "id": 3, "severity": "High", "status": "closed",
        "first_seen": first.isoformat() + "Z",
        "closed_at": closed.isoformat() + "Z",
    }
    result = compute_vuln_sla(vuln)
    assert result["sla_deadline_days"] == 30
    assert result["days_open"] == 35  # 40 - 5 = 35 days to close


def test_compute_kpis_empty():
    """KPIs on an empty database should return zeros."""
    kpi = compute_kpis()
    assert kpi.total_open == 0
    assert kpi.breach_rate_pct == 0.0
    assert kpi.mttr_days is None


def test_compute_kpis_with_data():
    """KPIs with known data should compute correctly."""
    conn = get_db()
    try:
        now = datetime.utcnow()
        # Add open critical vuln that's breached (15 days old)
        conn.execute(
            """INSERT INTO vulnerabilities (scanner_type, asset_hostname, title, severity, cvss_score,
               status, first_seen, last_seen)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            ("nessus", "test01", "Critical RCE", "Critical", 9.8,
             "open", (now - timedelta(days=15)).isoformat() + "Z", now.isoformat() + "Z"),
        )
        # Add closed vuln
        conn.execute(
            """INSERT INTO vulnerabilities (scanner_type, asset_hostname, title, severity, cvss_score,
               status, first_seen, last_seen, closed_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            ("nessus", "test02", "Closed Vuln", "High", 7.5,
             "closed", (now - timedelta(days=20)).isoformat() + "Z",
             now.isoformat() + "Z", (now - timedelta(days=5)).isoformat() + "Z"),
        )
        conn.commit()

        kpi = compute_kpis()
        assert kpi.total_open == 1
        assert kpi.total_closed == 1
        assert kpi.critical_open == 1
        assert kpi.breached_count == 1
        assert kpi.breach_rate_pct == 100.0
        assert kpi.mttr_days is not None
    finally:
        conn.close()

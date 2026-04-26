"""Unit tests for models and SLA logic."""

from datetime import datetime, timedelta
from src.models import severity_from_cvss, sla_deadline_days, Severity, SLAKPI


def test_severity_from_cvss_critical():
    assert severity_from_cvss(10.0) == Severity.CRITICAL
    assert severity_from_cvss(9.0) == Severity.CRITICAL
    assert severity_from_cvss(9.5) == Severity.CRITICAL


def test_severity_from_cvss_high():
    assert severity_from_cvss(7.0) == Severity.HIGH
    assert severity_from_cvss(8.9) == Severity.HIGH


def test_severity_from_cvss_medium():
    assert severity_from_cvss(4.0) == Severity.MEDIUM
    assert severity_from_cvss(6.9) == Severity.MEDIUM


def test_severity_from_cvss_low():
    assert severity_from_cvss(0.1) == Severity.LOW
    assert severity_from_cvss(3.9) == Severity.LOW


def test_severity_from_cvss_info():
    assert severity_from_cvss(0.0) == Severity.INFO


def test_sla_deadlines():
    assert sla_deadline_days(Severity.CRITICAL) == 7
    assert sla_deadline_days(Severity.HIGH) == 30
    assert sla_deadline_days(Severity.MEDIUM) == 90
    assert sla_deadline_days(Severity.LOW) == 180
    assert sla_deadline_days(Severity.INFO) == 365


def test_slakpi_to_dict():
    kpi = SLAKPI(
        total_open=10, total_closed=5, total_risk_accepted=2,
        breached_count=3, breach_rate_pct=30.0, mttr_days=14.5,
        critical_open=2, high_open=4, medium_open=3, low_open=1,
        avg_cvss=7.5,
    )
    d = kpi.to_dict()
    assert d["total_open"] == 10
    assert d["breach_rate_pct"] == 30.0
    assert d["mttr_days"] == 14.5
    assert d["critical_open"] == 2
    assert d["avg_cvss"] == 7.5


def test_slakpi_empty():
    kpi = SLAKPI()
    d = kpi.to_dict()
    assert d["total_open"] == 0
    assert d["breach_rate_pct"] == 0.0
    assert d["mttr_days"] is None
    assert d["avg_cvss"] == 0.0

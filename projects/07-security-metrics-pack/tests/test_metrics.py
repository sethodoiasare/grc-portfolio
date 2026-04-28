"""Tests for metrics computation engine."""

from src.models import IncidentRecord, AlertRecord, VulnerabilityRecord, MetricSeverity
from src.metrics import compute_mttd_mttr, compute_alert_quality, compute_vuln_sla


class TestMTTDMTTR:
    def test_empty_incidents_returns_zero(self):
        m = compute_mttd_mttr([])
        assert m.total_incidents == 0
        assert m.mttd_hours == 0
        assert m.mttr_hours == 0

    def test_all_resolved_incidents(self):
        incidents = [
            IncidentRecord("INC-001", "2026-04-01T09:00:00", "2026-04-01T10:00:00",
                          "2026-04-01T15:00:00", MetricSeverity.HIGH),
            IncidentRecord("INC-002", "2026-04-02T09:00:00", "2026-04-02T10:00:00",
                          "2026-04-02T14:00:00", MetricSeverity.MEDIUM),
        ]
        m = compute_mttd_mttr(incidents)
        assert m.total_incidents == 2
        assert m.open_incidents == 0
        assert m.mttr_hours == 1.0  # avg of 1h each
        assert m.mtt_resolve_hours == 5.5

    def test_open_incident_counted(self):
        incidents = [
            IncidentRecord("INC-001", "2026-04-01T09:00:00", "2026-04-01T10:00:00",
                          "2026-04-01T15:00:00", MetricSeverity.HIGH),
            IncidentRecord("INC-002", "2026-04-02T09:00:00", None, None, MetricSeverity.CRITICAL),
        ]
        m = compute_mttd_mttr(incidents)
        assert m.open_incidents == 1

    def test_severity_breakdown(self):
        incidents = [
            IncidentRecord("INC-001", "2026-04-01T09:00:00", "2026-04-01T10:00:00",
                          "2026-04-01T15:00:00", MetricSeverity.CRITICAL),
            IncidentRecord("INC-002", "2026-04-02T09:00:00", "2026-04-02T10:00:00",
                          "2026-04-02T14:00:00", MetricSeverity.CRITICAL),
        ]
        m = compute_mttd_mttr(incidents)
        assert "CRITICAL" in m.avg_by_severity
        assert m.avg_by_severity["CRITICAL"]["count"] == 2


class TestAlertQuality:
    def test_empty_alerts(self):
        a = compute_alert_quality([])
        assert a.total_alerts == 0
        assert a.precision_pct == 0.0

    def test_perfect_precision(self):
        alerts = [
            AlertRecord("A1", "2026-04-01T09:00:00", True, False, MetricSeverity.HIGH, "SIEM"),
            AlertRecord("A2", "2026-04-01T10:00:00", True, False, MetricSeverity.MEDIUM, "SIEM"),
        ]
        a = compute_alert_quality(alerts)
        assert a.true_positives == 2
        assert a.false_positives == 0
        assert a.precision_pct == 100.0

    def test_mixed_quality(self):
        alerts = [
            AlertRecord("A1", "2026-04-01T09:00:00", True, False, MetricSeverity.HIGH, "SIEM"),
            AlertRecord("A2", "2026-04-01T10:00:00", False, True, MetricSeverity.MEDIUM, "SIEM"),
            AlertRecord("A3", "2026-04-01T11:00:00", True, False, MetricSeverity.HIGH, "EDR"),
            AlertRecord("A4", "2026-04-01T12:00:00", False, True, MetricSeverity.LOW, "SIEM"),
        ]
        a = compute_alert_quality(alerts)
        assert a.true_positives == 2
        assert a.false_positives == 2
        assert a.precision_pct == 50.0
        assert a.false_positive_rate_pct == 50.0

    def test_by_source_breakdown(self):
        alerts = [
            AlertRecord("A1", "2026-04-01T09:00:00", True, False, MetricSeverity.HIGH, "SIEM"),
            AlertRecord("A2", "2026-04-01T10:00:00", False, True, MetricSeverity.MEDIUM, "EDR"),
        ]
        a = compute_alert_quality(alerts)
        assert "SIEM" in a.by_source
        assert "EDR" in a.by_source
        assert a.by_source["SIEM"]["precision_pct"] == 100.0
        assert a.by_source["EDR"]["precision_pct"] == 0.0


class TestVulnSLA:
    def test_empty_vulns(self):
        v = compute_vuln_sla([])
        assert v.total_vulnerabilities == 0
        assert v.sla_compliance_pct == 100.0

    def test_all_within_sla(self):
        vulns = [
            VulnerabilityRecord("V1", "2026-04-01T00:00:00", MetricSeverity.HIGH, 7.5,
                              "2026-04-10T00:00:00", 30, "server-01"),
        ]
        v = compute_vuln_sla(vulns)
        assert v.within_sla == 1
        assert v.breached == 0
        assert v.sla_compliance_pct == 100.0

    def test_breached_sla(self):
        vulns = [
            VulnerabilityRecord("V1", "2026-03-01T00:00:00", MetricSeverity.CRITICAL, 9.8,
                              "2026-04-01T00:00:00", 14, "server-01"),
        ]
        v = compute_vuln_sla(vulns)
        assert v.breached == 1
        assert v.critical_breached == 1
        assert v.sla_compliance_pct == 0.0

    def test_unfixed_critical_counted_as_breached(self):
        vulns = [
            VulnerabilityRecord("V1", "2026-04-01T00:00:00", MetricSeverity.CRITICAL, 9.8,
                              None, 14, "server-01"),
        ]
        v = compute_vuln_sla(vulns)
        assert v.breached == 1
        assert v.overdue_critical == 1

    def test_mixed_compliance(self):
        vulns = [
            VulnerabilityRecord("V1", "2026-04-01T00:00:00", MetricSeverity.HIGH, 7.5,
                              "2026-04-10T00:00:00", 30, "s1"),
            VulnerabilityRecord("V2", "2026-03-01T00:00:00", MetricSeverity.CRITICAL, 9.0,
                              "2026-04-01T00:00:00", 14, "s2"),
        ]
        v = compute_vuln_sla(vulns)
        assert v.within_sla == 1
        assert v.breached == 1
        assert v.sla_compliance_pct == 50.0

    def test_severity_breakdown(self):
        vulns = [
            VulnerabilityRecord("V1", "2026-04-01T00:00:00", MetricSeverity.CRITICAL, 9.8,
                              "2026-04-10T00:00:00", 14, "s1"),
            VulnerabilityRecord("V2", "2026-04-01T00:00:00", MetricSeverity.HIGH, 7.5,
                              "2026-04-10T00:00:00", 30, "s2"),
        ]
        v = compute_vuln_sla(vulns)
        assert "CRITICAL" in v.by_severity
        assert "HIGH" in v.by_severity

"""Tests for domain models."""

from src.models import (
    IncidentRecord, AlertRecord, VulnerabilityRecord,
    MTTDMTTR, AlertQuality, VulnSLA, MetricReport, MetricSeverity,
)


class TestIncidentRecord:
    def test_creation(self):
        inc = IncidentRecord("INC-001", "2026-04-01T09:00:00",
                            "2026-04-01T10:00:00", "2026-04-01T15:00:00",
                            MetricSeverity.HIGH, "SIEM")
        assert inc.incident_id == "INC-001"
        assert inc.severity == MetricSeverity.HIGH


class TestAlertRecord:
    def test_creation(self):
        a = AlertRecord("ALT-001", "2026-04-01T09:00:00", True, False,
                       MetricSeverity.HIGH, "SIEM", "Brute Force")
        assert a.is_true_positive
        assert not a.is_false_positive


class TestVulnerabilityRecord:
    def test_creation(self):
        v = VulnerabilityRecord("VULN-001", "2026-03-01T00:00:00",
                               MetricSeverity.CRITICAL, 9.8,
                               "2026-03-15T00:00:00", 14, "web-01")
        assert v.cvss_score == 9.8
        assert v.sla_days == 14


class TestMTTDMTTR:
    def test_to_dict(self):
        m = MTTDMTTR(mttd_hours=2.5, mttr_hours=1.0, mtt_resolve_hours=24.0,
                    total_incidents=10, open_incidents=2)
        d = m.to_dict()
        assert d["mttd_hours"] == 2.5
        assert d["mttr_hours"] == 1.0


class TestAlertQuality:
    def test_to_dict(self):
        a = AlertQuality(total_alerts=100, true_positives=80, false_positives=20,
                        precision_pct=80.0, false_positive_rate_pct=20.0)
        d = a.to_dict()
        assert d["precision_pct"] == 80.0


class TestVulnSLA:
    def test_to_dict(self):
        v = VulnSLA(total_vulnerabilities=50, within_sla=40, breached=10,
                   critical_breached=3, sla_compliance_pct=80.0,
                   mttr_vuln_hours=48.0, overdue_critical=2)
        d = v.to_dict()
        assert d["sla_compliance_pct"] == 80.0


class TestMetricReport:
    def test_to_dict(self):
        mttd = MTTDMTTR(2.5, 1.0, 24.0, 10, 2)
        aq = AlertQuality(100, 80, 20, 80.0, 20.0)
        vsla = VulnSLA(50, 40, 10, 3, 80.0, 48.0, 2)
        report = MetricReport(
            report_id="r1", generated_at="2026-04-28", period_start="2026-04-01",
            period_end="2026-04-30", mttd_mttr=mttd, alert_quality=aq, vuln_sla=vsla,
        )
        d = report.to_dict()
        assert d["report_id"] == "r1"
        assert d["rag_status"] in ("GREEN", "AMBER", "RED")

    def test_rag_scoring(self):
        mttd_good = MTTDMTTR(1.0, 0.5, 4.0, 5, 0)
        aq_good = AlertQuality(100, 95, 5, 95.0, 5.0)
        vsla_good = VulnSLA(50, 48, 2, 0, 96.0, 24.0, 0)
        report = MetricReport("r1", "2026", "", "", mttd_good, aq_good, vsla_good)
        assert report.rag_status() == "GREEN"

    def test_rag_red(self):
        mttd_bad = MTTDMTTR(48.0, 24.0, 72.0, 5, 2)
        aq_bad = AlertQuality(100, 60, 40, 60.0, 40.0)
        vsla_bad = VulnSLA(50, 20, 30, 10, 40.0, 168.0, 5)
        report = MetricReport("r1", "2026", "", "", mttd_bad, aq_bad, vsla_bad)
        assert report.rag_status() == "RED"

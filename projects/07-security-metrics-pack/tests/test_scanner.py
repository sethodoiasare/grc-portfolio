"""Tests for metrics scanner and report generation."""

import json
from src.scanner import compute
from src.models import MetricReport
from src.cli import _demo_incidents, _demo_alerts, _demo_vulns


class TestCompute:
    def test_returns_metric_report(self):
        report = compute(incidents=_demo_incidents(), alerts=_demo_alerts(), vulns=_demo_vulns())
        assert isinstance(report, MetricReport)
        assert report.mttd_mttr.total_incidents == 6
        assert report.alert_quality.total_alerts == 10
        assert report.vuln_sla.total_vulnerabilities == 8

    def test_demo_rag_status(self):
        report = compute(incidents=_demo_incidents(), alerts=_demo_alerts(), vulns=_demo_vulns())
        assert report.rag_status() in ("GREEN", "AMBER", "RED")

    def test_to_dict_serializable(self):
        report = compute(incidents=_demo_incidents(), alerts=_demo_alerts(), vulns=_demo_vulns())
        d = report.to_dict()
        assert isinstance(d["mttd_mttr"], dict)
        assert isinstance(d["alert_quality"], dict)
        assert isinstance(d["vuln_sla"], dict)
        json.dumps(d)

    def test_no_data_returns_zero_report(self):
        report = compute()
        assert report.mttd_mttr.total_incidents == 0
        assert report.alert_quality.total_alerts == 0
        assert report.vuln_sla.total_vulnerabilities == 0

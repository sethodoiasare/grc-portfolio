"""Tests for JSON reporter."""

import json
from src.scanner import compute
from src.reporter import export_json
from src.cli import _demo_incidents, _demo_alerts, _demo_vulns


def test_export_json_creates_file(tmp_path):
    report = compute(incidents=_demo_incidents(), alerts=_demo_alerts(), vulns=_demo_vulns())
    out = tmp_path / "report.json"
    result = export_json(report, out)
    assert result.exists()
    data = json.loads(result.read_text())
    assert data["mttd_mttr"]["total_incidents"] == 6
    assert data["alert_quality"]["total_alerts"] == 10
    assert data["vuln_sla"]["total_vulnerabilities"] == 8
    assert "rag_status" in data

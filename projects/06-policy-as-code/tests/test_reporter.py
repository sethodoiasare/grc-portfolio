"""Tests for JSON reporter."""

import json
from pathlib import Path
from src.scanner import scan
from src.reporter import export_json


def test_export_json_creates_file(tmp_path):
    report = scan([{"_policy_id": "IAM-003", "UserName": "alice", "MFAEnabled": True}])
    out = tmp_path / "report.json"
    result = export_json(report, out)
    assert result.exists()
    data = json.loads(result.read_text())
    assert data["engine"] == "python-native"
    assert data["compliance_rate_pct"] == 100.0


def test_export_json_contains_critical_failures(tmp_path):
    report = scan([
        {"_policy_id": "NET-001", "GroupId": "sg-bad", "SecurityGroupRules": [
            {"Protocol": "tcp", "FromPort": 22, "ToPort": 22, "CidrIp": "0.0.0.0/0"},
        ]},
    ])
    out = tmp_path / "report.json"
    export_json(report, out)
    data = json.loads(out.read_text())
    assert len(data["critical_failures"]) == 1

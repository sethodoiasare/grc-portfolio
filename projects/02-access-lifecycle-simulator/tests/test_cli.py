"""Tests for CLI demo mode and reporter."""

import json
import subprocess
import sys
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent.parent


class TestDemoMode:
    def test_demo_runs_and_creates_output(self, tmp_path):
        """Verify demo mode runs to completion and writes JSON output."""
        out_file = tmp_path / "audit-report.json"
        result = subprocess.run(
            [sys.executable, "-m", "src.cli", "scan", "--demo",
             "--output", str(out_file)],
            cwd=str(PROJECT_DIR),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"CLI failed:\n{result.stderr}"
        assert out_file.exists(), f"Output file not created at {out_file}"
        data = json.loads(out_file.read_text())
        assert "summary" in data
        assert "violations" in data

    def test_demo_finds_all_violation_types(self, tmp_path):
        """Demo data should produce at least one violation of each type."""
        out_file = tmp_path / "audit-report.json"
        result = subprocess.run(
            [sys.executable, "-m", "src.cli", "scan", "--demo",
             "--output", str(out_file)],
            cwd=str(PROJECT_DIR),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        data = json.loads(out_file.read_text())
        by_type = data["summary"]["by_type"]
        expected_types = {"LEAVER_ACTIVE", "ORPHANED", "MFA_MISSING", "SELF_APPROVAL"}
        found_types = set(by_type.keys())
        missing = expected_types - found_types
        assert not missing, f"Demo data missing violation types: {missing}"

    def test_cert_report_flag(self, tmp_path):
        """--cert-report flag includes certification items."""
        out_file = tmp_path / "audit-report.json"
        result = subprocess.run(
            [sys.executable, "-m", "src.cli", "scan", "--demo",
             "--output", str(out_file), "--cert-report"],
            cwd=str(PROJECT_DIR),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        data = json.loads(out_file.read_text())
        assert "access_certification_items" in data
        assert len(data["access_certification_items"]) > 0
        # Each item should have action, certify_by, control_id
        for item in data["access_certification_items"]:
            assert "action" in item
            assert item["action"] in ("REVOKE", "REVIEW", "CONFIRM")
            assert "certify_by" in item
            assert "control_id" in item

    def test_violations_have_control_mapping(self, tmp_path):
        """Each violation must include Vodafone control mapping."""
        out_file = tmp_path / "audit-report.json"
        subprocess.run(
            [sys.executable, "-m", "src.cli", "scan", "--demo",
             "--output", str(out_file)],
            cwd=str(PROJECT_DIR),
            capture_output=True,
            text=True,
        )
        data = json.loads(out_file.read_text())
        for v in data["violations"]:
            cm = v.get("control_mapping", {})
            assert "control" in cm, f"Missing control in violation {v.get('violation_id')}"
            assert "control_id" in cm
            assert "d_statement" in cm

    def test_summary_counts_match_violations(self, tmp_path):
        """Summary total must equal length of violations list."""
        out_file = tmp_path / "audit-report.json"
        subprocess.run(
            [sys.executable, "-m", "src.cli", "scan", "--demo",
             "--output", str(out_file)],
            cwd=str(PROJECT_DIR),
            capture_output=True,
            text=True,
        )
        data = json.loads(out_file.read_text())
        assert data["summary"]["total"] == len(data["violations"])


class TestReporter:
    def test_build_audit_report(self):
        from src.engine import run_all_checks
        from src.data import load_sample_data
        from src.reporter import build_audit_report

        ad, hr, itsm = load_sample_data()
        violations = run_all_checks(ad, hr, itsm)
        report = build_audit_report(violations, len(ad), len(hr), len(itsm))

        assert report.audit_date is not None
        assert report.summary["total"] == len(violations)
        assert "by_severity" in report.summary
        assert "by_type" in report.summary

    def test_export_json_writes_file(self, tmp_path):
        from src.engine import run_all_checks
        from src.data import load_sample_data
        from src.reporter import build_audit_report, export_json

        ad, hr, itsm = load_sample_data()
        violations = run_all_checks(ad, hr, itsm)
        report = build_audit_report(violations, len(ad), len(hr), len(itsm))
        out = tmp_path / "report.json"
        result = export_json(report, out)
        assert result.exists()
        data = json.loads(result.read_text())
        assert data["summary"]["total"] == len(violations)

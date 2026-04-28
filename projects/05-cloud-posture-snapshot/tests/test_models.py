"""Tests for data models."""

import json
from src.models import (
    PostureReport, PostureSummary, CheckResult,
    CheckStatus, Severity, Provider,
)


class TestEnums:
    def test_check_status_values(self):
        assert CheckStatus.PASS.value == "PASS"
        assert CheckStatus.FAIL.value == "FAIL"
        assert CheckStatus.NA.value == "NOT_APPLICABLE"

    def test_severity_values(self):
        assert Severity.CRITICAL.value == "CRITICAL"
        assert Severity.HIGH.value == "HIGH"
        assert Severity.MEDIUM.value == "MEDIUM"
        assert Severity.LOW.value == "LOW"

    def test_provider_values(self):
        assert Provider.AWS.value == "AWS"
        assert Provider.AZURE.value == "AZURE"
        assert Provider.GCP.value == "GCP"


class TestCheckResult:
    def test_to_dict(self):
        cr = CheckResult(
            check_id="1.1",
            check_title="Test check",
            status=CheckStatus.PASS,
            severity=Severity.HIGH,
            resource="test-resource",
            finding="Everything is fine.",
            remediation="Do nothing.",
            vodafone_control="Management of privileged access rights",
            d_statement="D1-D5",
        )
        d = cr.to_dict()
        assert d["check_id"] == "1.1"
        assert d["status"] == "PASS"
        assert d["severity"] == "HIGH"


class TestPostureSummary:
    def test_defaults(self):
        s = PostureSummary()
        assert s.total_checks == 0
        assert s.pass_rate_pct == 0.0

    def test_to_dict(self):
        s = PostureSummary(total_checks=10, passed=8, failed=2, pass_rate_pct=80.0)
        d = s.to_dict()
        assert d["total_checks"] == 10
        assert d["passed"] == 8


class TestPostureReport:
    def test_default_construction(self):
        r = PostureReport(provider="AWS", account_id="123", cis_benchmark_version="CIS v1.5")
        assert r.provider == "AWS"
        assert r.report_id
        assert r.generated_at

    def test_compute_summary_empty(self):
        r = PostureReport(provider="AWS", account_id="123", cis_benchmark_version="CIS v1.5")
        r.compute_summary()
        assert r.summary.total_checks == 0
        assert r.summary.pass_rate_pct == 0.0

    def test_compute_summary_with_findings(self):
        findings = [
            CheckResult("1.1", "Test", CheckStatus.PASS, Severity.HIGH, "res", "ok", "fix", "ctrl", "D1"),
            CheckResult("1.2", "Test", CheckStatus.FAIL, Severity.CRITICAL, "res", "bad", "fix", "ctrl", "D1"),
            CheckResult("1.3", "Test", CheckStatus.FAIL, Severity.HIGH, "res", "bad", "fix", "ctrl", "D1"),
            CheckResult("1.4", "Test", CheckStatus.PASS, Severity.MEDIUM, "res", "ok", "fix", "ctrl", "D1"),
            CheckResult("1.5", "Test", CheckStatus.NA, Severity.LOW, "res", "n/a", "fix", "ctrl", "D1"),
        ]
        r = PostureReport(provider="AWS", account_id="123", cis_benchmark_version="CIS v1.5", findings=findings)
        r.compute_summary()
        assert r.summary.total_checks == 5
        assert r.summary.passed == 2
        assert r.summary.failed == 2
        assert r.summary.not_applicable == 1
        assert r.summary.pass_rate_pct == 50.0  # 2/4 assessed
        assert r.summary.critical_failures == 1
        assert r.summary.high_failures == 1

    def test_rag_green(self):
        r = PostureReport(provider="AWS", account_id="123", cis_benchmark_version="CIS v1.5")
        r.summary.pass_rate_pct = 85.0
        assert r.rag_status() == "GREEN"

    def test_rag_amber(self):
        r = PostureReport(provider="AWS", account_id="123", cis_benchmark_version="CIS v1.5")
        r.summary.pass_rate_pct = 70.0
        assert r.rag_status() == "AMBER"

    def test_rag_red(self):
        r = PostureReport(provider="AWS", account_id="123", cis_benchmark_version="CIS v1.5")
        r.summary.pass_rate_pct = 45.0
        assert r.rag_status() == "RED"

    def test_to_dict(self):
        r = PostureReport(provider="AWS", account_id="123", cis_benchmark_version="CIS v1.5")
        r.compute_summary()
        d = r.to_dict()
        assert d["provider"] == "AWS"
        assert "summary" in d
        assert "findings" in d

    def test_critical_failures_filter(self):
        findings = [
            CheckResult("1.1", "T", CheckStatus.FAIL, Severity.CRITICAL, "r", "f", "fix", "c", "D1"),
            CheckResult("1.2", "T", CheckStatus.FAIL, Severity.HIGH, "r", "f", "fix", "c", "D1"),
            CheckResult("1.3", "T", CheckStatus.FAIL, Severity.MEDIUM, "r", "f", "fix", "c", "D1"),
            CheckResult("1.4", "T", CheckStatus.PASS, Severity.LOW, "r", "f", "fix", "c", "D1"),
        ]
        r = PostureReport(provider="AWS", account_id="123", cis_benchmark_version="CIS v1.5", findings=findings)
        r.compute_summary()
        assert len(r.critical_failures) == 2  # CRITICAL + HIGH

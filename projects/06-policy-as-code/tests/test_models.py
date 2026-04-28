"""Tests for domain models."""

from src.models import (
    Policy, PolicyResult, PolicyReport, Verdict, Severity,
    POLICIES, VODAFONE_CONTROLS,
)


class TestPoliciesInventory:
    def test_all_12_policies_defined(self):
        assert len(POLICIES) == 12

    def test_every_policy_has_id_title_category_severity(self):
        for p in POLICIES:
            assert p["id"]
            assert p["title"]
            assert p["category"]
            assert isinstance(p["severity"], Severity)
            assert p["rego_file"].endswith(".rego")

    def test_categories_distributed(self):
        cats = {p["category"] for p in POLICIES}
        assert cats == {"iam", "encryption", "logging", "networking"}

    def test_severities_present(self):
        sevs = {p["severity"] for p in POLICIES}
        assert Severity.CRITICAL in sevs
        assert Severity.HIGH in sevs

    def test_rego_files_exist(self):
        from pathlib import Path
        policies_dir = Path(__file__).parent.parent / "src" / "policies"
        for p in POLICIES:
            assert (policies_dir / p["rego_file"]).exists(), f"Missing {p['rego_file']}"


class TestVodafoneMappings:
    def test_all_categories_mapped(self):
        for cat in ["iam", "encryption", "logging", "networking"]:
            assert cat in VODAFONE_CONTROLS
            assert "name" in VODAFONE_CONTROLS[cat]
            assert "d_statement" in VODAFONE_CONTROLS[cat]


class TestPolicyResult:
    def test_to_dict(self):
        r = PolicyResult(
            policy_id="IAM-001", policy_title="Test", category="iam",
            verdict=Verdict.COMPLIANT, severity=Severity.CRITICAL,
            resource="test-policy", finding="All good",
            remediation="Fix it", vodafone_control="IAM Control", d_statement="D1-D5",
        )
        d = r.to_dict()
        assert d["verdict"] == "COMPLIANT"
        assert d["severity"] == "CRITICAL"


class TestPolicyReport:
    def test_compliance_rate(self):
        r = PolicyReport(
            report_id="r1", generated_at="2026-01-01", engine="python-native",
            total_policies=10, compliant=8, non_compliant=2, errors=0,
        )
        assert r.compliance_rate_pct == 80.0

    def test_compliance_rate_zero_denominator(self):
        r = PolicyReport(
            report_id="r1", generated_at="2026-01-01", engine="python-native",
            total_policies=0, compliant=0, non_compliant=0, errors=0,
        )
        assert r.compliance_rate_pct == 0.0

    def test_rag_green(self):
        r = PolicyReport("r1", "2026", "python-native", 10, 9, 1, 0)
        assert r.rag_status() == "GREEN"

    def test_rag_amber(self):
        r = PolicyReport("r1", "2026", "python-native", 10, 7, 3, 0)
        assert r.rag_status() == "AMBER"

    def test_rag_red(self):
        r = PolicyReport("r1", "2026", "python-native", 10, 5, 5, 0)
        assert r.rag_status() == "RED"

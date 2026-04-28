"""Tests for data models."""

import json
from src.models import (
    Verdict, Severity, ArtifactType, EvidencePackage, CoverageSummary,
    FindingSummary, ToolArtifact, SASTFinding, SCAFinding, SecretFinding,
    DASTFinding,
)


class TestVerdict:
    def test_values(self):
        assert Verdict.SATISFIED.value == "SATISFIED"
        assert Verdict.PARTIAL.value == "PARTIAL"
        assert Verdict.NOT_MET.value == "NOT_MET"
        assert Verdict.NOT_APPLICABLE.value == "NOT_APPLICABLE"


class TestSeverity:
    def test_values(self):
        assert Severity.CRITICAL.value == "critical"
        assert Severity.HIGH.value == "high"
        assert Severity.MEDIUM.value == "medium"
        assert Severity.LOW.value == "low"


class TestCoverageSummary:
    def test_defaults(self):
        cs = CoverageSummary()
        assert cs.D1_SAST == Verdict.NOT_APPLICABLE
        assert cs.D7_FINDINGS_TRACKING == Verdict.NOT_APPLICABLE

    def test_to_dict_serializable(self):
        cs = CoverageSummary()
        d = cs.to_dict()
        assert d["D1_SAST"] == "NOT_APPLICABLE"
        assert isinstance(d["D1_SAST"], str)
        json.dumps(d)  # should not raise


class TestEvidencePackage:
    def test_default_construction(self):
        pkg = EvidencePackage(project="test")
        assert pkg.project == "test"
        assert pkg.control == "DevSecOps"
        assert pkg.evidence_package_id
        assert len(pkg.evidence_package_id) == 36  # UUID4
        assert pkg.generated_at

    def test_to_dict(self):
        pkg = EvidencePackage(project="dict-test", branch="main")
        d = pkg.to_dict()
        assert d["project"] == "dict-test"
        assert d["branch"] == "main"
        assert "coverage_summary" in d

    def test_custom_coverage(self):
        cs = CoverageSummary()
        cs.D1_SAST = Verdict.SATISFIED
        pkg = EvidencePackage(project="cov-test", coverage_summary=cs)
        assert pkg.to_dict()["coverage_summary"]["D1_SAST"] == "SATISFIED"


class TestToolArtifact:
    def test_creation(self):
        ta = ToolArtifact(
            tool="semgrep",
            artifact_type=ArtifactType.SAST,
            timestamp="2026-01-01T00:00:00Z",
            scope="repo",
            status="FAIL",
            findings_count=3,
            maps_to=["D1"],
        )
        d = ta.__dict__ if hasattr(ta, '__dict__') else {}
        assert ta.tool == "semgrep"
        assert ta.status == "FAIL"


class TestFindings:
    def test_sast_finding(self):
        f = SASTFinding(
            check_id="test-001",
            path="app.py",
            severity=Severity.HIGH,
            message="Test finding",
            line=42,
        )
        assert f.check_id == "test-001"
        assert f.line == 42

    def test_sca_finding(self):
        f = SCAFinding(
            package_name="django",
            version="3.2.0",
            vulnerability_id="CVE-2024-001",
            severity=Severity.CRITICAL,
            fixed_version="3.2.25",
        )
        assert f.package_name == "django"
        assert f.fixed_version == "3.2.25"

    def test_secret_finding(self):
        f = SecretFinding(
            description="AWS key",
            file_path=".env",
            severity=Severity.HIGH,
            commit="abc123",
        )
        assert f.description == "AWS key"

    def test_dast_finding(self):
        f = DASTFinding(
            alert_name="XSS",
            risk_level=Severity.MEDIUM,
            url="https://example.com",
            description="Reflected XSS",
            cwe_id="79",
        )
        assert f.alert_name == "XSS"
        assert f.cwe_id == "79"

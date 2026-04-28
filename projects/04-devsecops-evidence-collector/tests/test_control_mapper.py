"""Tests for control mapping logic."""

from src.control_mapper import (
    map_coverage, build_findings_summary, identify_blocking_findings,
    identify_gaps, build_audit_narrative, D_STATEMENTS,
)
from src.models import (
    CoverageSummary, FindingSummary, Verdict, ToolArtifact, ArtifactType,
    SASTFinding, SCAFinding, SecretFinding, DASTFinding, Severity,
)


class TestDStatements:
    def test_all_eight_defined(self):
        for d in [f"D{i}" for i in range(1, 9)]:
            assert d in D_STATEMENTS
            assert D_STATEMENTS[d]["title"]
            assert D_STATEMENTS[d]["requirement"]

    def test_standard_refs(self):
        assert "CYBER/STD/014" in D_STATEMENTS["D1"]["standard_ref"]
        assert "CYBER_062" in D_STATEMENTS["D7"]["standard_ref"]


class TestMapCoverage:
    def test_all_tools_satisfied(self):
        artifacts = [
            ToolArtifact("semgrep", ArtifactType.SAST, "", "repo", "PASS", 0, ["D1"]),
            ToolArtifact("pip-audit", ArtifactType.SCA, "", "repo", "PASS", 0, ["D2"]),
            ToolArtifact("gitleaks", ArtifactType.SECRETS, "", "repo", "PASS", 0, ["D3"]),
            ToolArtifact("owasp-zap", ArtifactType.DAST, "", "staging", "PASS", 0, ["D4"]),
            ToolArtifact("github-actions", ArtifactType.PIPELINE_LOG, "", "ci", "PASS", 8, ["D5", "D6"]),
        ]
        coverage = map_coverage(artifacts)
        assert coverage.D1_SAST == Verdict.SATISFIED
        assert coverage.D2_SCA == Verdict.SATISFIED
        assert coverage.D3_SECRETS == Verdict.SATISFIED
        assert coverage.D4_DAST == Verdict.SATISFIED
        assert coverage.D5_REVIEW_GATE == Verdict.SATISFIED
        assert coverage.D6_BLOCKING_POLICY == Verdict.SATISFIED

    def test_tools_with_findings_partial(self):
        artifacts = [
            ToolArtifact("semgrep", ArtifactType.SAST, "", "repo", "FAIL", 4, ["D1"]),
            ToolArtifact("gitleaks", ArtifactType.SECRETS, "", "repo", "FAIL", 3, ["D3"]),
        ]
        coverage = map_coverage(artifacts)
        assert coverage.D1_SAST == Verdict.PARTIAL
        assert coverage.D3_SECRETS == Verdict.PARTIAL
        assert coverage.D2_SCA == Verdict.NOT_MET  # missing tool
        assert coverage.D4_DAST == Verdict.NOT_MET

    def test_no_artifacts_not_met(self):
        coverage = map_coverage([])
        assert coverage.D1_SAST == Verdict.NOT_MET
        assert coverage.D2_SCA == Verdict.NOT_MET
        assert coverage.D3_SECRETS == Verdict.NOT_MET
        assert coverage.D4_DAST == Verdict.NOT_MET

    def test_d7_d8_not_applicable(self):
        artifacts = [ToolArtifact("semgrep", ArtifactType.SAST, "", "repo", "PASS", 0, ["D1"])]
        coverage = map_coverage(artifacts)
        assert coverage.D7_FINDINGS_TRACKING == Verdict.NOT_APPLICABLE
        assert coverage.D8_DEVELOPER_TRAINING == Verdict.NOT_APPLICABLE

    def test_to_dict(self):
        coverage = map_coverage([])
        d = coverage.to_dict()
        assert d["D1_SAST"] == "NOT_MET"
        assert isinstance(d["D1_SAST"], str)


class TestBuildFindingsSummary:
    def test_empty(self):
        summary = build_findings_summary([], [], [], [])
        assert summary.sast["critical"] == 0
        assert summary.sca["high"] == 0
        assert summary.secrets["count"] == 0
        assert summary.dast["low"] == 0

    def test_counts_by_severity(self):
        sast = [
            SASTFinding("check1", "a.py", Severity.CRITICAL, "msg"),
            SASTFinding("check2", "b.py", Severity.HIGH, "msg"),
            SASTFinding("check3", "c.py", Severity.MEDIUM, "msg"),
            SASTFinding("check4", "d.py", Severity.LOW, "msg"),
        ]
        summary = build_findings_summary(sast, [], [], [])
        assert summary.sast["critical"] == 1
        assert summary.sast["high"] == 1
        assert summary.sast["medium"] == 1
        assert summary.sast["low"] == 1

    def test_secret_types(self):
        secrets = [
            SecretFinding("AWS key", ".env", Severity.HIGH, rule_id="aws-key"),
            SecretFinding("API key", "config.py", Severity.HIGH, rule_id="generic-api"),
            SecretFinding("JWT", "test.py", Severity.MEDIUM, rule_id="jwt-secret"),
        ]
        summary = build_findings_summary([], [], secrets, [])
        assert summary.secrets["count"] == 3
        assert len(summary.secrets["types"]) == 3


class TestIdentifyBlockingFindings:
    def test_critical_and_high_blocking(self):
        sast = [
            SASTFinding("c1", "a.py", Severity.CRITICAL, "critical issue"),
            SASTFinding("c2", "b.py", Severity.HIGH, "high issue"),
            SASTFinding("c3", "c.py", Severity.MEDIUM, "medium issue"),
        ]
        blocking = identify_blocking_findings(sast, [], [])
        assert len(blocking) == 2

    def test_sca_blocking(self):
        sca = [
            SCAFinding("pkg", "1.0", "CVE-2023-001", Severity.CRITICAL),
            SCAFinding("pkg2", "2.0", "CVE-2023-002", Severity.LOW),
        ]
        blocking = identify_blocking_findings([], sca, [])
        assert len(blocking) == 1
        assert blocking[0]["source"] == "SCA"

    def test_dast_blocking(self):
        dast = [
            DASTFinding("XSS", Severity.HIGH, "url1", "desc"),
            DASTFinding("Info leak", Severity.LOW, "url2", "desc"),
        ]
        blocking = identify_blocking_findings([], [], dast)
        assert len(blocking) == 1
        assert blocking[0]["source"] == "DAST"


class TestIdentifyGaps:
    def test_no_artifacts(self):
        coverage = map_coverage([])
        gaps = identify_gaps(coverage, 0)
        assert len(gaps) > 0
        assert any("No security scanning artifacts" in g for g in gaps)

    def test_all_satisfied_no_gaps(self):
        artifacts = [
            ToolArtifact("semgrep", ArtifactType.SAST, "", "repo", "PASS", 0, ["D1"]),
            ToolArtifact("pip-audit", ArtifactType.SCA, "", "repo", "PASS", 0, ["D2"]),
            ToolArtifact("gitleaks", ArtifactType.SECRETS, "", "repo", "PASS", 0, ["D3"]),
            ToolArtifact("owasp-zap", ArtifactType.DAST, "", "staging", "PASS", 0, ["D4"]),
            ToolArtifact("github-actions", ArtifactType.PIPELINE_LOG, "", "ci", "PASS", 8, ["D5", "D6"]),
        ]
        coverage = map_coverage(artifacts)
        gaps = identify_gaps(coverage, len(artifacts))
        # D7 and D8 are still NOT_APPLICABLE — those should show as gaps
        d7_gaps = [g for g in gaps if "D7" in g]
        d8_gaps = [g for g in gaps if "D8" in g]
        assert len(d7_gaps) == 0  # NOT_APPLICABLE is not a gap — it means not expected
        assert len(d8_gaps) == 0


class TestBuildAuditNarrative:
    def test_generates_narrative(self):
        coverage = map_coverage([])
        summary = build_findings_summary([], [], [], [])
        narrative = build_audit_narrative(coverage, summary, [], "test-project")
        assert "test-project" in narrative
        assert len(narrative) > 100

    def test_narrative_mentions_blocking(self):
        coverage = map_coverage([])
        summary = build_findings_summary([], [], [], [])
        blocking = [{"source": "SAST", "severity": "critical", "check_id": "test"}]
        narrative = build_audit_narrative(coverage, summary, blocking, "test")
        assert "critical" in narrative.lower()

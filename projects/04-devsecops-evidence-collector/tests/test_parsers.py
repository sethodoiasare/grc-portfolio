"""Tests for tool output parsers."""

import json
from pathlib import Path
from src.parsers import (
    parse_semgrep, parse_pip_audit, parse_gitleaks, parse_zap, parse_pipeline_log,
    _normalise_severity, _zap_risk_to_severity,
)
from src.models import Severity, ArtifactType

SAMPLE_DIR = Path(__file__).resolve().parent.parent / "data" / "sample_outputs"


class TestNormaliseSeverity:
    def test_critical(self):
        assert _normalise_severity("critical") == Severity.CRITICAL
        assert _normalise_severity("error") == Severity.CRITICAL

    def test_high(self):
        assert _normalise_severity("high") == Severity.HIGH
        assert _normalise_severity("warning") == Severity.HIGH

    def test_medium(self):
        assert _normalise_severity("medium") == Severity.MEDIUM
        assert _normalise_severity("moderate") == Severity.MEDIUM

    def test_low(self):
        assert _normalise_severity("low") == Severity.LOW

    def test_default_info(self):
        assert _normalise_severity("unknown") == Severity.INFO

    def test_case_insensitive(self):
        assert _normalise_severity("CRITICAL") == Severity.CRITICAL
        assert _normalise_severity("High") == Severity.HIGH


class TestZapRiskToSeverity:
    def test_numeric_3(self):
        assert _zap_risk_to_severity("3") == Severity.HIGH

    def test_numeric_2(self):
        assert _zap_risk_to_severity("2") == Severity.MEDIUM

    def test_numeric_1(self):
        assert _zap_risk_to_severity("1") == Severity.LOW

    def test_numeric_0(self):
        assert _zap_risk_to_severity("0") == Severity.INFO

    def test_string_risk(self):
        assert _zap_risk_to_severity("High") == Severity.HIGH


class TestParseSemgrep:
    def test_parse_sample_file(self):
        findings, artifact = parse_semgrep(SAMPLE_DIR / "semgrep.json")

        assert len(findings) == 4
        assert artifact.tool == "semgrep"
        assert artifact.artifact_type == ArtifactType.SAST
        assert artifact.status == "FAIL"
        assert artifact.findings_count == 4
        assert "D1" in artifact.maps_to

    def test_finding_fields(self):
        findings, _ = parse_semgrep(SAMPLE_DIR / "semgrep.json")
        f = findings[0]
        assert f.check_id
        assert f.path
        assert isinstance(f.severity, Severity)
        assert f.message

    def test_severity_counts(self):
        findings, artifact = parse_semgrep(SAMPLE_DIR / "semgrep.json")
        counts = artifact.raw_summary
        assert counts["critical"] == 2  # two "error" severity
        assert counts["high"] == 2     # two "warning" severity

    def test_empty_results(self):
        raw = json.dumps({"results": [], "semgrep_version": "1.0"})
        findings, artifact = parse_semgrep(raw)
        assert len(findings) == 0
        assert artifact.status == "PASS"

    def test_parse_from_string(self):
        raw = SAMPLE_DIR.joinpath("semgrep.json").read_text()
        findings, artifact = parse_semgrep(raw)
        assert len(findings) == 4


class TestParsePipAudit:
    def test_parse_sample_file(self):
        findings, artifact = parse_pip_audit(SAMPLE_DIR / "pip-audit.json")

        assert len(findings) == 4  # 1+1+2 from 3 vulnerable packages
        assert artifact.tool == "pip-audit"
        assert artifact.artifact_type == ArtifactType.SCA
        assert "D2" in artifact.maps_to

    def test_finding_severity(self):
        findings, _ = parse_pip_audit(SAMPLE_DIR / "pip-audit.json")
        severities = [f.severity for f in findings]
        assert Severity.CRITICAL in severities
        assert Severity.HIGH in severities
        assert Severity.MEDIUM in severities

    def test_empty_dependencies(self):
        raw = json.dumps({"dependencies": []})
        findings, artifact = parse_pip_audit(raw)
        assert len(findings) == 0
        assert artifact.status == "PASS"


class TestParseGitleaks:
    def test_parse_sample_file(self):
        findings, artifact = parse_gitleaks(SAMPLE_DIR / "gitleaks.json")

        assert len(findings) == 3
        assert artifact.tool == "gitleaks"
        assert artifact.artifact_type == ArtifactType.SECRETS
        assert "D3" in artifact.maps_to

    def test_finding_has_description(self):
        findings, _ = parse_gitleaks(SAMPLE_DIR / "gitleaks.json")
        assert all(f.description for f in findings)
        assert all(f.file_path for f in findings)

    def test_secret_types_tracked(self):
        findings, artifact = parse_gitleaks(SAMPLE_DIR / "gitleaks.json")
        assert len(artifact.raw_summary["types"]) > 0

    def test_empty_list(self):
        raw = json.dumps([])
        findings, artifact = parse_gitleaks(raw)
        assert len(findings) == 0
        assert artifact.status == "PASS"


class TestParseZap:
    def test_parse_sample_file(self):
        findings, artifact = parse_zap(SAMPLE_DIR / "zap.json")

        assert len(findings) == 5
        assert artifact.tool == "owasp-zap"
        assert artifact.artifact_type == ArtifactType.DAST
        assert "D4" in artifact.maps_to

    def test_severity_mapping(self):
        findings, _ = parse_zap(SAMPLE_DIR / "zap.json")
        severities = {f.risk_level for f in findings}
        assert Severity.HIGH in severities  # risk 3
        assert Severity.MEDIUM in severities  # risk 2

    def test_cwe_ids(self):
        findings, _ = parse_zap(SAMPLE_DIR / "zap.json")
        cwes = [f.cwe_id for f in findings if f.cwe_id]
        assert "79" in cwes
        assert "89" in cwes


class TestParsePipelineLog:
    def test_parse_sample_file(self):
        artifact = parse_pipeline_log(SAMPLE_DIR / "pipeline.log")

        assert artifact.tool == "github-actions"
        assert artifact.artifact_type == ArtifactType.PIPELINE_LOG
        assert "D5" in artifact.maps_to
        assert "D6" in artifact.maps_to
        assert artifact.raw_summary["gates_detected"] is True

    def test_empty_log(self):
        artifact = parse_pipeline_log("")
        assert artifact.status == "WARNING"
        assert len(artifact.raw_summary["steps"]) == 0

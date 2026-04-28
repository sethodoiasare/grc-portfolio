"""Tests for evidence packager."""

import json
from pathlib import Path
from src.packager import build_package, export_package
from src.models import EvidencePackage

SAMPLE_DIR = Path(__file__).resolve().parent.parent / "data" / "sample_outputs"


class TestBuildPackage:
    def test_build_empty(self):
        pkg = build_package()
        assert isinstance(pkg, EvidencePackage)
        assert pkg.control == "DevSecOps"
        assert pkg.evidence_package_id
        assert pkg.generated_at

    def test_build_with_all_samples(self):
        pkg = build_package(
            semgrep_path=SAMPLE_DIR / "semgrep.json",
            pip_audit_path=SAMPLE_DIR / "pip-audit.json",
            gitleaks_path=SAMPLE_DIR / "gitleaks.json",
            zap_path=SAMPLE_DIR / "zap.json",
            pipeline_log_path=SAMPLE_DIR / "pipeline.log",
            project="test-app",
            branch="main",
            commit_sha="abc123",
        )

        assert pkg.project == "test-app"
        assert pkg.branch == "main"
        assert pkg.commit_sha == "abc123"
        assert len(pkg.artifacts) == 5
        assert pkg.coverage_summary.D1_SAST is not None
        assert pkg.audit_narrative

    def test_build_partial_inputs(self):
        pkg = build_package(
            semgrep_path=SAMPLE_DIR / "semgrep.json",
            gitleaks_path=SAMPLE_DIR / "gitleaks.json",
        )
        assert len(pkg.artifacts) == 2
        assert pkg.coverage_summary.D1_SAST is not None
        assert pkg.coverage_summary.D2_SCA is not None

    def test_missing_file_skipped(self):
        pkg = build_package(semgrep_path=Path("/nonexistent/semgrep.json"))
        assert len(pkg.artifacts) == 0

    def test_blocking_findings_populated(self):
        pkg = build_package(
            semgrep_path=SAMPLE_DIR / "semgrep.json",
            pip_audit_path=SAMPLE_DIR / "pip-audit.json",
            zap_path=SAMPLE_DIR / "zap.json",
        )
        assert len(pkg.blocking_findings) > 0

    def test_findings_summary_has_counts(self):
        pkg = build_package(
            semgrep_path=SAMPLE_DIR / "semgrep.json",
            pip_audit_path=SAMPLE_DIR / "pip-audit.json",
        )
        assert pkg.findings_summary.sast["critical"] > 0
        assert pkg.findings_summary.sca["high"] > 0

    def test_gaps_identified(self):
        pkg = build_package(semgrep_path=SAMPLE_DIR / "semgrep.json")
        gaps = pkg.gaps
        assert any("D2" in g or "D3" in g for g in gaps)

    def test_standard_references_default(self):
        pkg = build_package()
        assert "CYBER/STD/014" in pkg.standard_references
        assert "CYBER_062" in pkg.standard_references

    def test_artifacts_have_correct_types(self):
        pkg = build_package(
            semgrep_path=SAMPLE_DIR / "semgrep.json",
            pip_audit_path=SAMPLE_DIR / "pip-audit.json",
            gitleaks_path=SAMPLE_DIR / "gitleaks.json",
            zap_path=SAMPLE_DIR / "zap.json",
            pipeline_log_path=SAMPLE_DIR / "pipeline.log",
        )
        artifact_tools = [a.tool for a in pkg.artifacts]
        assert "semgrep" in artifact_tools
        assert "pip-audit" in artifact_tools
        assert "gitleaks" in artifact_tools
        assert "owasp-zap" in artifact_tools
        assert "github-actions" in artifact_tools


class TestExportPackage:
    def test_export_to_file(self, tmp_path):
        pkg = build_package(project="export-test")
        output = tmp_path / "output" / "evidence-package.json"
        result = export_package(pkg, output)
        assert result.exists()
        data = json.loads(result.read_text())
        assert data["project"] == "export-test"
        assert data["control"] == "DevSecOps"

    def test_to_dict_serializable(self, tmp_path):
        pkg = build_package(
            semgrep_path=SAMPLE_DIR / "semgrep.json",
            project="serial-test",
        )
        output = tmp_path / "pkg.json"
        export_package(pkg, output)
        data = json.loads(output.read_text())
        assert "coverage_summary" in data
        assert "findings_summary" in data
        assert "artifacts" in data

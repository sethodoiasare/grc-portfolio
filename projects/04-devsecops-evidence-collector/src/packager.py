"""Build the complete DevSecOps audit evidence package."""

import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

from .models import EvidencePackage, CoverageSummary
from .parsers import (
    parse_semgrep, parse_pip_audit, parse_gitleaks, parse_zap, parse_pipeline_log,
)
from .control_mapper import (
    map_coverage, build_findings_summary,
    identify_blocking_findings, identify_gaps, build_audit_narrative,
)


def build_package(
    semgrep_path: Optional[str | Path] = None,
    pip_audit_path: Optional[str | Path] = None,
    gitleaks_path: Optional[str | Path] = None,
    zap_path: Optional[str | Path] = None,
    pipeline_log_path: Optional[str | Path] = None,
    project: str = "",
    branch: str = "",
    commit_sha: str = "",
    pipeline_run: str = "",
    audit_period: str = "",
) -> EvidencePackage:
    """Parse all available tool outputs and assemble a complete evidence package."""

    sast_findings, sca_findings, secret_findings, dast_findings = [], [], [], []
    artifacts = []
    scope = _scope_from_project(project)

    if semgrep_path and Path(semgrep_path).exists():
        sast_findings, sast_artifact = parse_semgrep(semgrep_path, scope)
        artifacts.append(sast_artifact)

    if pip_audit_path and Path(pip_audit_path).exists():
        sca_findings, sca_artifact = parse_pip_audit(pip_audit_path, scope)
        artifacts.append(sca_artifact)

    if gitleaks_path and Path(gitleaks_path).exists():
        secret_findings, gitleaks_artifact = parse_gitleaks(gitleaks_path, scope)
        artifacts.append(gitleaks_artifact)

    if zap_path and Path(zap_path).exists():
        dast_findings, zap_artifact = parse_zap(zap_path, scope)
        artifacts.append(zap_artifact)

    if pipeline_log_path and Path(pipeline_log_path).exists():
        pipeline_artifact = parse_pipeline_log(pipeline_log_path, scope)
        artifacts.append(pipeline_artifact)

    coverage = map_coverage(artifacts)
    findings = build_findings_summary(sast_findings, sca_findings, secret_findings, dast_findings)
    blocking = identify_blocking_findings(sast_findings, sca_findings, dast_findings)
    gaps = identify_gaps(coverage, len(artifacts))
    narrative = build_audit_narrative(coverage, findings, blocking, project or "this repository")

    pkg = EvidencePackage(
        generated_at=datetime.now(timezone.utc).isoformat(),
        project=project,
        branch=branch,
        commit_sha=commit_sha,
        pipeline_run=pipeline_run,
        audit_period=audit_period,
        coverage_summary=coverage,
        findings_summary=findings,
        blocking_findings=blocking,
        gaps=gaps,
        audit_narrative=narrative,
        artifacts=artifacts,
    )
    return pkg


def export_package(pkg: EvidencePackage, output_path: str | Path) -> Path:
    """Write the evidence package to a JSON file."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(pkg.to_dict(), indent=2, default=str))
    return output_path


def _scope_from_project(project: str) -> str:
    if not project:
        return "repository"
    return project

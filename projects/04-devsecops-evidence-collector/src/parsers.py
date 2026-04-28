"""Parse output from Semgrep, pip-audit, Gitleaks, and OWASP ZAP."""

import json
from typing import Optional
from pathlib import Path

from .models import (
    SASTFinding, SCAFinding, SecretFinding, DASTFinding,
    Severity, ToolArtifact, ArtifactType,
)

DEFAULT_SCOPE = "repository"


def parse_semgrep(raw: str | Path, scope: str = DEFAULT_SCOPE) -> tuple[list[SASTFinding], ToolArtifact]:
    """Parse Semgrep JSON output into findings and artifact metadata."""
    if isinstance(raw, Path):
        raw = raw.read_text()
    data = json.loads(raw)

    findings = []
    results = data.get("results", [])
    for r in results:
        sev = _normalise_severity(r.get("extra", {}).get("severity", "info"))
        findings.append(SASTFinding(
            check_id=r.get("check_id", "unknown"),
            path=r.get("path", "unknown"),
            severity=sev,
            message=r.get("extra", {}).get("message", ""),
            line=r.get("start", {}).get("line"),
            rule_name=r.get("check_id"),
        ))

    artifact = ToolArtifact(
        tool="semgrep",
        artifact_type=ArtifactType.SAST,
        timestamp=data.get("semgrep_version", ""),
        scope=scope,
        status="PASS" if not findings else "FAIL",
        findings_count=len(findings),
        maps_to=["D1"],
        raw_summary=_severity_counts(findings),
    )
    return findings, artifact


def parse_pip_audit(raw: str | Path, scope: str = DEFAULT_SCOPE) -> tuple[list[SCAFinding], ToolArtifact]:
    """Parse pip-audit JSON output into findings and artifact metadata."""
    if isinstance(raw, Path):
        raw = raw.read_text()
    data = json.loads(raw)

    findings = []
    for entry in data.get("dependencies", data if isinstance(data, list) else []):
        for vuln in entry.get("vulns", []):
            sev = _normalise_severity(vuln.get("severity", "medium"))
            findings.append(SCAFinding(
                package_name=entry.get("name", "unknown"),
                version=entry.get("version", "unknown"),
                vulnerability_id=vuln.get("id", "unknown"),
                severity=sev,
                fixed_version=vuln.get("fix_versions", [None])[0] if vuln.get("fix_versions") else None,
                advisory=vuln.get("advisory", {}).get("url") if isinstance(vuln.get("advisory"), dict) else None,
            ))

    artifact = ToolArtifact(
        tool="pip-audit",
        artifact_type=ArtifactType.SCA,
        timestamp="",
        scope=scope,
        status="PASS" if not findings else "FAIL",
        findings_count=len(findings),
        maps_to=["D2"],
        raw_summary=_severity_counts(findings),
    )
    return findings, artifact


def parse_gitleaks(raw: str | Path, scope: str = DEFAULT_SCOPE) -> tuple[list[SecretFinding], ToolArtifact]:
    """Parse Gitleaks JSON output into findings and artifact metadata."""
    if isinstance(raw, Path):
        raw = raw.read_text()
    data = json.loads(raw)

    findings = []
    for entry in data if isinstance(data, list) else [data]:
        sev_field = entry.get("Severity", entry.get("severity", "medium"))
        sev = _normalise_severity(sev_field)
        findings.append(SecretFinding(
            description=entry.get("Description", entry.get("description", "Secret detected")),
            file_path=entry.get("File", entry.get("file", "unknown")),
            severity=sev,
            commit=entry.get("Commit", entry.get("commit")),
            rule_id=entry.get("RuleID", entry.get("rule_id")),
            line=entry.get("StartLine", entry.get("line")),
        ))

    types_found = list({f.rule_id or f.description for f in findings})
    artifact = ToolArtifact(
        tool="gitleaks",
        artifact_type=ArtifactType.SECRETS,
        timestamp="",
        scope=scope,
        status="PASS" if not findings else "FAIL",
        findings_count=len(findings),
        maps_to=["D3"],
        raw_summary={"count": len(findings), "types": types_found},
    )
    return findings, artifact


def parse_zap(raw: str | Path, scope: str = "staging") -> tuple[list[DASTFinding], ToolArtifact]:
    """Parse OWASP ZAP JSON report into findings and artifact metadata."""
    if isinstance(raw, Path):
        raw = raw.read_text()
    data = json.loads(raw)

    findings = []
    alerts = []
    if "site" in data:
        for site in data.get("site", []):
            alerts.extend(site.get("alerts", []))
    else:
        alerts = data.get("alerts", data if isinstance(data, list) else [])

    for alert in alerts:
        risk = alert.get("risk", alert.get("riskcode", "0"))
        sev = _zap_risk_to_severity(risk)
        findings.append(DASTFinding(
            alert_name=alert.get("name", alert.get("alert", "Unknown")),
            risk_level=sev,
            url=alert.get("url", ""),
            description=alert.get("desc", alert.get("description", "")),
            cwe_id=str(alert.get("cweid", "")) or None,
            confidence=alert.get("confidence", ""),
        ))

    artifact = ToolArtifact(
        tool="owasp-zap",
        artifact_type=ArtifactType.DAST,
        timestamp="",
        scope=scope,
        status="PASS" if not findings else "FAIL",
        findings_count=len(findings),
        maps_to=["D4"],
        raw_summary=_severity_counts(findings),
    )
    return findings, artifact


def parse_pipeline_log(raw: str | Path, scope: str = "ci") -> ToolArtifact:
    """Parse a CI pipeline run log to extract step execution evidence for D5/D6."""
    if isinstance(raw, Path):
        raw = raw.read_text()

    steps = _extract_pipeline_steps(raw)
    gated = any("block" in s.lower() or "require" in s.lower() for s in steps)
    status = "PASS" if steps else "WARNING"

    return ToolArtifact(
        tool="github-actions",
        artifact_type=ArtifactType.PIPELINE_LOG,
        timestamp="",
        scope=scope,
        status=status,
        findings_count=len(steps),
        maps_to=["D5", "D6"],
        raw_summary={"steps": steps, "gates_detected": gated},
    )


def _normalise_severity(raw: str) -> Severity:
    raw_lower = str(raw).strip().lower()
    mapping = {
        "critical": Severity.CRITICAL, "error": Severity.CRITICAL,
        "high": Severity.HIGH, "warning": Severity.HIGH,
        "medium": Severity.MEDIUM, "moderate": Severity.MEDIUM, "warn": Severity.MEDIUM,
        "low": Severity.LOW, "note": Severity.LOW,
    }
    return mapping.get(raw_lower, Severity.INFO)


def _zap_risk_to_severity(risk: str) -> Severity:
    mapping = {"3": Severity.HIGH, "2": Severity.MEDIUM, "1": Severity.LOW, "0": Severity.INFO}
    if isinstance(risk, str) and risk.isdigit():
        return mapping.get(risk, Severity.INFO)
    return _normalise_severity(risk)


def _severity_counts(findings: list) -> dict:
    counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for f in findings:
        sev = _get_finding_severity(f)
        if sev.value in counts:
            counts[sev.value] += 1
    return counts


def _get_finding_severity(finding) -> Severity:
    for attr in ["severity", "risk_level", "severity_level"]:
        val = getattr(finding, attr, None)
        if val and isinstance(val, Severity):
            return val
    return Severity.INFO


def _extract_pipeline_steps(raw: str) -> list[str]:
    steps = []
    for line in raw.strip().splitlines():
        for prefix in ("Run ", "Step ", "✓ ", "✗ ", "[") :
            if line.strip().startswith(prefix):
                steps.append(line.strip())
                break
    return steps

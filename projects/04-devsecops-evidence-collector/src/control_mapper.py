"""Map tool outputs to Vodafone DevSecOps D1-D8 control statements."""

from .models import (
    Verdict, CoverageSummary, FindingSummary, ToolArtifact,
    SASTFinding, SCAFinding, SecretFinding, DASTFinding,
    Severity,
)

# D1-D8 control statements from the Vodafone DevSecOps pipeline scanning framework
D_STATEMENTS = {
    "D1": {
        "id": "D1",
        "title": "SAST integrated in CI pipeline",
        "requirement": "Static Application Security Testing (SAST) is integrated into the CI pipeline and runs on every commit/PR.",
        "standard_ref": "CYBER/STD/014",
    },
    "D2": {
        "id": "D2",
        "title": "SCA/dependency scanning in pipeline",
        "requirement": "Software Composition Analysis (SCA) scans dependencies for known vulnerabilities on every build.",
        "standard_ref": "CYBER/STD/014",
    },
    "D3": {
        "id": "D3",
        "title": "Secrets/credential scanning in pipeline",
        "requirement": "Secrets and credential scanning runs in the CI pipeline to prevent accidental exposure.",
        "standard_ref": "CYBER/STD/014",
    },
    "D4": {
        "id": "D4",
        "title": "DAST performed on test/staging environment",
        "requirement": "Dynamic Application Security Testing (DAST) is performed against deployed test/staging environments.",
        "standard_ref": "CYBER/STD/014",
    },
    "D5": {
        "id": "D5",
        "title": "Security scan results reviewed before merge/deploy",
        "requirement": "Security scan results are reviewed and acknowledged before code merge or production deployment.",
        "standard_ref": "CYBER/STD/014",
    },
    "D6": {
        "id": "D6",
        "title": "Critical/high findings block deployment",
        "requirement": "Critical and high-severity security findings must block deployment until remediated or risk-accepted.",
        "standard_ref": "CYBER/STD/014",
    },
    "D7": {
        "id": "D7",
        "title": "Security findings tracked to closure",
        "requirement": "All security findings are tracked in a backlog or ticketing system through to verified closure.",
        "standard_ref": "CYBER_062",
    },
    "D8": {
        "id": "D8",
        "title": "Security training for developers",
        "requirement": "Developers complete secure coding training with records maintained for audit.",
        "standard_ref": "CYBER_062",
    },
}


def map_coverage(artifacts: list[ToolArtifact]) -> CoverageSummary:
    """Determine D1-D8 coverage based on which tool artifacts are present."""
    tool_map = {
        "D1": ["semgrep"],
        "D2": ["pip-audit"],
        "D3": ["gitleaks"],
        "D4": ["owasp-zap"],
        "D5": ["github-actions"],
        "D6": ["github-actions"],
        "D7": [],   # external system, not auto-detected
        "D8": [],   # external system, not auto-detected
    }

    artifact_tools = [a.tool for a in artifacts]
    coverage = CoverageSummary()

    for d_key, required_tools in tool_map.items():
        if not required_tools:
            coverage_val = Verdict.NOT_APPLICABLE
        elif all(t in artifact_tools for t in required_tools):
            matching = [a for a in artifacts if a.tool in required_tools]
            if all(a.status == "PASS" for a in matching):
                coverage_val = Verdict.SATISFIED
            else:
                coverage_val = Verdict.PARTIAL
        else:
            coverage_val = Verdict.NOT_MET

        setattr(coverage, f"D{d_key[1]}_{_control_label(d_key)}", coverage_val)

    return coverage


def build_findings_summary(
    sast_findings: list[SASTFinding],
    sca_findings: list[SCAFinding],
    secret_findings: list[SecretFinding],
    dast_findings: list[DASTFinding],
) -> FindingSummary:
    """Aggregate severity counts across all tool categories."""

    def _count_by_sev(findings, sev_attr="severity"):
        counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for f in findings:
            sev = getattr(f, sev_attr)
            if sev.value in counts:
                counts[sev.value] += 1
        return counts

    secret_types = list({f.rule_id or f.description for f in secret_findings})

    return FindingSummary(
        sast=_count_by_sev(sast_findings),
        sca=_count_by_sev(sca_findings),
        secrets={"count": len(secret_findings), "types": secret_types},
        dast=_count_by_sev(dast_findings, "risk_level"),
    )


def identify_blocking_findings(
    sast_findings: list[SASTFinding],
    sca_findings: list[SCAFinding],
    dast_findings: list[DASTFinding],
) -> list[dict]:
    """Extract critical and high findings that should block deployment (D6)."""
    blocking = []

    for f in sast_findings:
        if f.severity in (Severity.CRITICAL, Severity.HIGH):
            blocking.append({
                "source": "SAST",
                "check_id": f.check_id,
                "path": f.path,
                "severity": f.severity.value,
                "message": f.message,
            })

    for f in sca_findings:
        if f.severity in (Severity.CRITICAL, Severity.HIGH):
            blocking.append({
                "source": "SCA",
                "package": f.package_name,
                "version": f.version,
                "vulnerability_id": f.vulnerability_id,
                "severity": f.severity.value,
            })

    for f in dast_findings:
        if f.risk_level in (Severity.CRITICAL, Severity.HIGH):
            blocking.append({
                "source": "DAST",
                "alert": f.alert_name,
                "url": f.url,
                "severity": f.risk_level.value,
                "cwe_id": f.cwe_id,
            })

    return blocking


def identify_gaps(coverage: CoverageSummary, artifact_count: int) -> list[str]:
    """Identify control gaps based on coverage assessment."""
    gaps = []
    labels = {
        "D1_SAST": ("D1: SAST tool present but findings not resolved", "D1: SAST not integrated in CI pipeline"),
        "D2_SCA": ("D2: SCA tool present but vulnerable dependencies found", "D2: SCA/dependency scanning not present in pipeline"),
        "D3_SECRETS": ("D3: Secrets scan detected exposed credentials", "D3: Secrets scanning not configured in CI pipeline"),
        "D4_DAST": ("D4: DAST detected vulnerabilities in target", "D4: DAST not performed against test/staging environment"),
        "D5_REVIEW_GATE": ("D5: No evidence of security scan review before merge/deploy", "D5: No evidence of security scan review before merge/deploy"),
        "D6_BLOCKING_POLICY": ("D6: No evidence that critical/high findings block deployment", "D6: No evidence that critical/high findings block deployment"),
        "D7_FINDINGS_TRACKING": ("D7: Findings tracking evidence not available (external system)", "D7: Findings tracking evidence not available (external system)"),
        "D8_DEVELOPER_TRAINING": ("D8: Developer security training records not available (external system)", "D8: Developer security training records not available (external system)"),
    }

    for attr, (partial_msg, not_met_msg) in labels.items():
        verdict = getattr(coverage, attr)
        if verdict == Verdict.NOT_MET:
            gaps.append(not_met_msg)
        elif verdict == Verdict.PARTIAL:
            gaps.append(partial_msg)

    if artifact_count == 0:
        gaps.insert(0, "No security scanning artifacts were provided")

    return gaps


def build_audit_narrative(
    coverage: CoverageSummary,
    findings_summary: FindingSummary,
    blocking_findings: list[dict],
    project_name: str = "this project",
) -> str:
    """Generate a formal 150-200 word audit narrative."""
    satisfied = sum(1 for v in coverage.to_dict().values() if v == "SATISFIED")
    total_detected = sum(len(blocking_findings) for _ in [1])

    total_findings = (
        sum(findings_summary.sast.values())
        + sum(findings_summary.sca.values())
        + findings_summary.secrets["count"]
        + sum(findings_summary.dast.values())
    )

    critical_high = (
        findings_summary.sast.get("critical", 0) + findings_summary.sast.get("high", 0)
        + findings_summary.sca.get("critical", 0) + findings_summary.sca.get("high", 0)
        + findings_summary.dast.get("critical", 0) + findings_summary.dast.get("high", 0)
    )

    blocking_count = len(blocking_findings)

    narrative = (
        f"A DevSecOps pipeline audit was conducted for {project_name}. "
        f"Of the eight DevSecOps control statements (D1-D8), {satisfied} were satisfied "
        f"through automated pipeline evidence. "
    )

    if blocking_count > 0:
        narrative += (
            f"A total of {blocking_count} critical or high-severity findings were identified "
            f"that should block deployment per control D6. "
        )

    narrative += (
        f"Automated scanning detected {total_findings} findings across SAST, SCA, secrets, and DAST scans. "
        f"Of these, {critical_high} were critical or high severity. "
    )

    not_met = sum(1 for v in coverage.to_dict().values() if v == "NOT_MET")
    if not_met > 0:
        narrative += (
            f"{not_met} control statements could not be verified as the required tool evidence was not present. "
        )

    narrative += (
        "Controls D7 (findings tracking) and D8 (developer training) require evidence from external systems "
        "and are noted as not assessed through automated pipeline scanning. "
        "The findings in this report should be reviewed by the Security Chapter Lead and "
        "tracked through the established vulnerability management process."
    )

    return narrative


def _control_label(d_key: str) -> str:
    labels = {
        "D1": "SAST", "D2": "SCA", "D3": "SECRETS", "D4": "DAST",
        "D5": "REVIEW_GATE", "D6": "BLOCKING_POLICY",
        "D7": "FINDINGS_TRACKING", "D8": "DEVELOPER_TRAINING",
    }
    return labels.get(d_key, d_key)

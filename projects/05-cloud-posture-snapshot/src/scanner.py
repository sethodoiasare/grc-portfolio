"""Orchestrate CIS benchmark checks across cloud providers."""

from .checks.aws import AWSChecker
from .checks.azure import AzureChecker
from .checks.gcp import GCPChecker
from .checks.registry import BENCHMARK_VERSIONS
from .models import PostureReport, CheckResult


def scan_aws(account_id: str = "111122223333", mock: bool = True, session=None) -> PostureReport:
    """Run all AWS CIS v1.5 checks and return a populated PostureReport."""
    checker = AWSChecker(account_id=account_id, mock=mock, session=session)
    findings = checker.run_all()
    return _build_report("AWS", account_id, findings)


def scan_azure(subscription_id: str = "00000000-0000-0000-0000-000000000000", mock: bool = True) -> PostureReport:
    """Run all Azure CIS v2.0 checks and return a populated PostureReport."""
    checker = AzureChecker(subscription_id=subscription_id, mock=mock)
    findings = checker.run_all()
    return _build_report("AZURE", subscription_id, findings)


def scan_gcp(project_id: str = "my-gcp-project", mock: bool = True) -> PostureReport:
    """Run all GCP CIS v2.0 checks and return a populated PostureReport."""
    checker = GCPChecker(project_id=project_id, mock=mock)
    findings = checker.run_all()
    return _build_report("GCP", project_id, findings)


def _build_report(provider: str, account_id: str, findings: list[CheckResult]) -> PostureReport:
    report = PostureReport(
        provider=provider,
        account_id=account_id,
        cis_benchmark_version=BENCHMARK_VERSIONS.get(provider, ""),
        findings=findings,
    )
    report.compute_summary()
    report.management_summary = _generate_management_summary(report)
    return report


def _generate_management_summary(report: PostureReport) -> str:
    """Generate a management-facing executive summary of the posture results."""
    rag = report.rag_status()
    s = report.summary

    rag_descriptor = {
        "GREEN": "The cloud environment demonstrates strong alignment with CIS hardening standards.",
        "AMBER": "The cloud environment shows partial alignment with CIS hardening standards. Targeted remediation is required.",
        "RED": "The cloud environment has significant gaps against CIS hardening standards. Urgent remediation is needed.",
    }

    summary = (
        f"Cloud Posture Assessment — {report.provider} ({report.cis_benchmark_version}). "
        f"Account: {report.account_id}. "
        f"Overall RAG Status: {rag}. "
    )

    summary += rag_descriptor.get(rag, "")

    summary += (
        f" {s.total_checks} CIS checks executed: {s.passed} passed, {s.failed} failed, "
        f"{s.not_applicable} not applicable. Pass rate: {s.pass_rate_pct}%. "
    )

    if s.critical_failures > 0:
        summary += (
            f"{s.critical_failures} critical-severity failures require immediate attention. "
        )

    if s.high_failures > 0:
        summary += (
            f"{s.high_failures} high-severity failures should be remediated within 30 days. "
        )

    top_critical = [f for f in report.critical_failures if f.get("severity") == "CRITICAL"][:3]
    if top_critical:
        summary += "Top critical findings: "
        for cf in top_critical:
            summary += f"[{cf['check_id']}] {cf['check_title']} — {cf['finding'][:120]}. "

    if rag == "RED":
        summary += (
            "Immediate action: Address all critical failures within 7 days. "
            "Engage the Security Chapter Lead for remediation prioritisation. "
            "A follow-up assessment should be scheduled within 30 days to verify closure."
        )
    elif rag == "AMBER":
        summary += (
            "Recommended action: Prioritise critical and high-severity findings for remediation. "
            "Target a pass rate above 80% (GREEN) within 60 days. "
            "Align remediation with Vodafone CYBER_038 hardening standards."
        )
    else:
        summary += (
            "The environment meets the CIS hardening baseline. "
            "Continue routine posture assessments and monitor for configuration drift. "
            "Review any MEDIUM or LOW findings during the next scheduled audit cycle."
        )

    return summary

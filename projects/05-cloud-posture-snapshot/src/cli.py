"""CLI for Cloud Posture Snapshot — CIS benchmark assessment across AWS, Azure, GCP."""

import argparse
import sys
from pathlib import Path

from .scanner import scan_aws, scan_azure, scan_gcp
from .reporter import export_json, export_pdf
from .checks.registry import AWS_CHECKS, AZURE_CHECKS, GCP_CHECKS


def main():
    parser = argparse.ArgumentParser(
        description="Cloud Posture Snapshot — CIS benchmark assessment for AWS, Azure, GCP",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  cloud-posture scan --provider aws                         # Mock mode (no credentials needed)
  cloud-posture scan --provider azure --format both         # JSON + PDF report
  cloud-posture scan --provider aws --account-id 123456789  # Specific account
  cloud-posture scan --provider gcp --output my-report.json
  cloud-posture list-checks --provider aws                  # List all AWS CIS checks
  cloud-posture summary posture-report.json                 # Print summary from saved report
        """,
    )
    sub = parser.add_subparsers(dest="command", help="Commands")

    # ── scan ──────────────────────────────────────────────────
    scan_parser = sub.add_parser("scan", help="Run CIS benchmark scan")
    scan_parser.add_argument("--provider", "-p", required=True, choices=["aws", "azure", "gcp"],
                             help="Cloud provider")
    scan_parser.add_argument("--account-id", default="",
                             help="Account/subscription/project ID")
    scan_parser.add_argument("--mock", action="store_true", default=True,
                             help="Use mock mode (default, no credentials needed)")
    scan_parser.add_argument("--live", dest="mock", action="store_false",
                             help="Use live cloud SDK calls (requires credentials)")
    scan_parser.add_argument("--output", "-o", type=Path, default=Path("posture-report.json"),
                             help="Output path (default: posture-report.json)")
    scan_parser.add_argument("--format", "-f", choices=["json", "pdf", "both"], default="json",
                             help="Output format (default: json)")

    # ── list-checks ───────────────────────────────────────────
    list_parser = sub.add_parser("list-checks", help="List available CIS checks for a provider")
    list_parser.add_argument("--provider", "-p", required=True, choices=["aws", "azure", "gcp"],
                             help="Cloud provider")

    # ── summary ───────────────────────────────────────────────
    summary_parser = sub.add_parser("summary", help="Print summary from a saved posture report")
    summary_parser.add_argument("report", type=Path, help="Path to posture report JSON")

    args = parser.parse_args()

    if args.command == "list-checks":
        return _list_checks(args.provider)

    if args.command == "summary":
        return _print_summary(args.report)

    if args.command == "scan":
        return _run_scan(args)

    if args.command is None:
        parser.print_help()
        return


def _run_scan(args):
    provider = args.provider
    account_id = args.account_id or {
        "aws": "111122223333",
        "azure": "00000000-0000-0000-0000-000000000000",
        "gcp": "my-gcp-project",
    }.get(provider, "")

    print(f"Running {provider.upper()} CIS benchmark scan...")

    if provider == "aws":
        report = scan_aws(account_id=account_id, mock=args.mock)
    elif provider == "azure":
        report = scan_azure(subscription_id=account_id, mock=args.mock)
    elif provider == "gcp":
        report = scan_gcp(project_id=account_id, mock=args.mock)

    s = report.summary
    rag = report.rag_status()
    print(f"  {s.total_checks} checks: {s.passed} passed, {s.failed} failed, "
          f"{s.not_applicable} NA — {s.pass_rate_pct}% pass rate — RAG: {rag}")

    if s.critical_failures:
        print(f"  {s.critical_failures} critical-severity failures")
    if s.high_failures:
        print(f"  {s.high_failures} high-severity failures")

    json_path = export_json(report, args.output)
    print(f"JSON report written to {json_path}")

    if args.format in ("pdf", "both"):
        pdf_path = args.output.with_suffix(".pdf")
        try:
            export_pdf(report, pdf_path)
            print(f"PDF report written to {pdf_path}")
        except ImportError as e:
            print(f"PDF skipped: {e}")
        except Exception as e:
            print(f"PDF generation failed: {e}")

    # Print top 3 critical failures
    if report.critical_failures:
        print("\nTop critical findings:")
        for cf in report.critical_failures[:3]:
            print(f"  [{cf['severity']}] {cf['check_id']} {cf['check_title']}: "
                  f"{cf['finding'][:100]}")

    # Print at-a-glance findings table
    print(f"\n{'ID':<8} {'Status':<16} {'Severity':<12} {'Title'}")
    print("-" * 80)
    for f in report.findings:
        if f.status.value == "NOT_APPLICABLE":
            continue
        print(f"{f.check_id:<8} {f.status.value:<16} {f.severity.value:<12} {f.check_title}")


def _list_checks(provider: str):
    registry = {"aws": AWS_CHECKS, "azure": AZURE_CHECKS, "gcp": GCP_CHECKS}
    checks = registry.get(provider, [])
    print(f"\n{provider.upper()} CIS Benchmark Checks ({len(checks)} checks):\n")
    print(f"{'ID':<8} {'Section':<10} {'Severity':<12} {'Title'}")
    print("-" * 80)
    for c in checks:
        print(f"{c['id']:<8} {c['section']:<10} {c['severity']:<12} {c['title']}")


def _print_summary(report_path: Path):
    import json
    data = json.loads(report_path.read_text())
    summary = data.get("summary", {})
    print(f"\nPosture Report: {data.get('provider', '?')} — {data.get('account_id', '?')}")
    print(f"CIS Benchmark: {data.get('cis_benchmark_version', '?')}")
    print(f"Generated: {data.get('generated_at', '?')}")
    print(f"\nTotal: {summary.get('total_checks', 0)} checks")
    print(f"  Passed:  {summary.get('passed', 0)}")
    print(f"  Failed:  {summary.get('failed', 0)}")
    print(f"  N/A:     {summary.get('not_applicable', 0)}")
    print(f"  Pass rate: {summary.get('pass_rate_pct', 0)}%")
    print(f"  Critical failures: {summary.get('critical_failures', 0)}")
    print(f"  High failures: {summary.get('high_failures', 0)}")
    print(f"\nManagement Summary:\n{data.get('management_summary', 'N/A')}")


if __name__ == "__main__":
    main()

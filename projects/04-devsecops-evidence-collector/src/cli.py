"""CLI for building DevSecOps audit evidence packages locally."""

import argparse
import json
import sys
from pathlib import Path

from .packager import build_package, export_package
from .signer import sign_package, verify_package
from .models import EvidencePackage


def main():
    parser = argparse.ArgumentParser(
        description="DevSecOps Audit Evidence Collector",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  devsecops-evidence --semgrep semgrep.json --gitleaks gitleaks.json
  devsecops-evidence --all-from-dir ./scan-results/ --project my-app --branch main
  devsecops-evidence --verify evidence-package.json
        """,
    )
    parser.add_argument("--semgrep", type=Path, help="Path to Semgrep JSON output")
    parser.add_argument("--pip-audit", type=Path, help="Path to pip-audit JSON output")
    parser.add_argument("--gitleaks", type=Path, help="Path to Gitleaks JSON output")
    parser.add_argument("--zap", type=Path, help="Path to OWASP ZAP JSON report")
    parser.add_argument("--pipeline-log", type=Path, help="Path to CI pipeline log")
    parser.add_argument("--all-from-dir", type=Path, help="Directory containing all scan outputs (auto-detects)")
    parser.add_argument("--project", default="", help="Project name")
    parser.add_argument("--branch", default="", help="Git branch")
    parser.add_argument("--commit", default="", help="Commit SHA")
    parser.add_argument("--pipeline-run", default="", help="Pipeline run ID or URL")
    parser.add_argument("--audit-period", default="", help="Audit period (e.g. FY25-Q3)")
    parser.add_argument("--output", "-o", type=Path, default=Path("evidence-package.json"),
                        help="Output path for evidence package JSON")
    parser.add_argument("--sign", action="store_true", help="HMAC-sign the output package")
    parser.add_argument("--verify", type=Path, help="Verify a signed evidence package")
    parser.add_argument("--json", action="store_true", help="Print package as JSON to stdout")

    args = parser.parse_args()

    if args.verify:
        _handle_verify(args.verify)
        return

    if args.all_from_dir:
        args = _auto_detect(args)

    pkg = build_package(
        semgrep_path=args.semgrep,
        pip_audit_path=getattr(args, 'pip_audit', None),
        gitleaks_path=args.gitleaks,
        zap_path=args.zap,
        pipeline_log_path=args.pipeline_log,
        project=args.project,
        branch=args.branch,
        commit_sha=args.commit,
        pipeline_run=args.pipeline_run,
        audit_period=args.audit_period,
    )

    if args.sign:
        pkg = sign_package(pkg)

    output_path = export_package(pkg, args.output)
    print(f"Evidence package written to {output_path}")

    if pkg.signature:
        print(f"Signature: {pkg.signature[:16]}...")

    if pkg.blocking_findings:
        print(f"\nBlocking findings: {len(pkg.blocking_findings)} critical/high")
        for bf in pkg.blocking_findings:
            print(f"  [{bf['severity'].upper()}] {bf.get('source', '')}: {bf.get('check_id', bf.get('vulnerability_id', bf.get('alert', '')))}")

    if pkg.gaps:
        print(f"\nGaps identified:")
        for g in pkg.gaps:
            print(f"  - {g}")

    if args.json:
        print(json.dumps(pkg.to_dict(), indent=2, default=str))


def _auto_detect(args) -> argparse.Namespace:
    d = args.all_from_dir
    if (d / "semgrep.json").exists(): args.semgrep = d / "semgrep.json"
    if (d / "semgrep-output.json").exists(): args.semgrep = d / "semgrep-output.json"
    if (d / "pip-audit.json").exists(): args.pip_audit = d / "pip-audit.json"
    if (d / "gitleaks.json").exists(): args.gitleaks = d / "gitleaks.json"
    if (d / "gitleaks-report.json").exists(): args.gitleaks = d / "gitleaks-report.json"
    if (d / "zap.json").exists(): args.zap = d / "zap.json"
    if (d / "zap-report.json").exists(): args.zap = d / "zap-report.json"
    if (d / "pipeline.log").exists(): args.pipeline_log = d / "pipeline.log"
    return args


def _handle_verify(path: Path):
    data = json.loads(path.read_text())
    sig = data.pop("signature", None)
    pkg = EvidencePackage(**{k: v for k, v in data.items() if k != "signature"})
    pkg.signature = sig

    if verify_package(pkg):
        print(f"VALID: {path}")
    else:
        print(f"INVALID (or unsigned): {path}")
        sys.exit(1)


if __name__ == "__main__":
    main()

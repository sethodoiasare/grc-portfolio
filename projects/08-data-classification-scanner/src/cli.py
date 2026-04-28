"""CLI for Data Classification Scanner."""

import argparse
import sys
import json
from pathlib import Path

from .scanner import scan
from .reporter import export_json
from .models import CLASSIFICATION_RULES


def main():
    parser = argparse.ArgumentParser(
        prog="data-classifier",
        description="Data Classification Scanner — PII/PCI/PHI/Secrets detection",
    )
    sub = parser.add_subparsers(dest="command")

    scan_p = sub.add_parser("scan", help="Scan files/directories for sensitive data")
    scan_p.add_argument("path", type=Path, nargs="?", default=None,
                        help="File or directory to scan (omit with --demo)")
    scan_p.add_argument("--output", "-o", type=Path, default=Path("classification-report.json"))
    scan_p.add_argument("--extensions", "-e", nargs="+", help="File extensions to scan (e.g. .py .json .txt)")
    scan_p.add_argument("--demo", action="store_true", help="Run against built-in demo data")

    list_p = sub.add_parser("list-rules", help="List all classification rules")
    list_p.add_argument("--category", "-c", choices=["PII", "PCI", "PHI", "SECRETS"])

    args = parser.parse_args()

    if args.command == "scan":
        if args.demo:
            _generate_demo_files()
            scan_path = Path("data/demo_scan")
        elif args.path:
            scan_path = args.path
        else:
            print("Error: path required (or use --demo)")
            sys.exit(1)

        if not scan_path.exists():
            print(f"Error: path '{scan_path}' does not exist")
            sys.exit(1)

        report = scan(scan_path, args.extensions)
        path = export_json(report, args.output)
        _print_summary(report)
        print(f"\nReport saved to {path}")

    elif args.command == "list-rules":
        rules = CLASSIFICATION_RULES
        if args.category:
            from .models import DataCategory
            cat = DataCategory(args.category)
            rules = [r for r in rules if r["category"] == cat]
        print(f"\n{'ID':<12} {'Category':<10} {'Severity':<10} Title")
        print("-" * 85)
        for r in rules:
            print(f"{r['id']:<12} {r['category'].value:<10} {r['severity'].value:<10} {r['title']}")
        print(f"\n{rules.__len__()} classification rules.")

    else:
        parser.print_help()


def _print_summary(report):
    print(f"\n{'='*60}")
    print(f"  Data Classification Scan Results")
    print(f"{'='*60}")
    print(f"  Files Scanned:            {report.total_files_scanned}")
    print(f"  Total Matches:            {report.total_matches}")
    print(f"  Files with Findings:      {report.files_with_findings}")
    print(f"  RAG Status:               {report.rag_status()}")
    print(f"  Critical: {report.critical_findings}  High: {report.high_findings}  "
          f"Medium: {report.medium_findings}  Low: {report.low_findings}")
    if report.by_category:
        print(f"  By Category: {json.dumps(report.by_category)}")
    print(f"{'='*60}")


def _generate_demo_files():
    """Create demo files with realistic sensitive data patterns."""
    import os
    demo_dir = Path("data/demo_scan")
    demo_dir.mkdir(parents=True, exist_ok=True)

    (demo_dir / "config.json").write_text(json.dumps({
        "database": {
            "connection_string": "postgresql://admin:SuperSecret123!@db.internal:5432/production",
            "api_key": "api_key='sk-proj-abc123def456ghi789jkl'",
        },
        "aws": {
            "access_key": "AKIAIOSFODNN7EXAMPLE",
            "secret": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY=="
        },
    }, indent=2))

    (demo_dir / "users.csv").write_text(
        "name,email,phone,ssn,notes\n"
        "John Doe,john.doe@company.com,+447911123456,,\n"
        "Jane Smith,jane.smith@gmail.com,,123-45-6789,US customer\n"
        "Test User,,,000-12-3456,invalid SSN\n"
    )

    (demo_dir / "README.md").write_text(
        "# Project Config\n\n"
        "Contact: admin@example.com\n"
        "Private key material below:\n"
        "-----BEGIN RSA PRIVATE KEY-----\n"
        "MIIEpAIBAAKCAQEA0Z3...\n"
        "-----END RSA PRIVATE KEY-----\n"
    )

    (demo_dir / "payments.log").write_text(
        "2026-04-01 09:00:00 Payment processed: card=4111111111111111 amount=99.99\n"
        "2026-04-01 09:01:00 Payment failed: card=5500000000000004 cvv=123\n"
        "2026-04-01 09:02:00 Refund: card=340000000000009 amount=50.00\n"
    )

    print(f"Demo files generated in {demo_dir}/")


if __name__ == "__main__":
    main()

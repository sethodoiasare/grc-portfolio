"""CLI for Security Control Coverage Mapper."""

import argparse
import sys
from pathlib import Path

from .models import CoverageStatus
from .frameworks import get_framework, list_frameworks
from .parser import parse_policy_document
from .mapper import map_coverage
from .reporter import print_summary, save_json_report, save_csv_report
from .demo_policy import get_demo_policy_text


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="coverage-mapper",
        description="Security Control Coverage Mapper — map policy documents "
                    "against ISO 27001, NIST CSF, CIS v8, and Vodafone controls.",
    )
    sub = parser.add_subparsers(dest="command")

    scan_p = sub.add_parser("scan", help="Map policy document against control frameworks")
    scan_p.add_argument("--file", "-f", type=Path, help="Path to policy document (.txt, .md, .pdf, .docx)")
    scan_p.add_argument("--framework", "-fw", default="all",
                        choices=["iso27001", "nist_csf", "cis_v8", "vodafone", "all"],
                        help="Framework to map against (default: all)")
    scan_p.add_argument("--output", "-o", type=Path, default=Path("data/coverage-report.json"),
                        help="Output path for JSON report")
    scan_p.add_argument("--csv", "-c", type=Path, default=None,
                        help="Optional output path for CSV report")
    scan_p.add_argument("--demo", action="store_true",
                        help="Run against built-in demo policy document")

    list_fw = sub.add_parser("list-frameworks", help="List available control frameworks")

    args = parser.parse_args()

    if args.command == "list-frameworks":
        fws = list_frameworks()
        print("\nAvailable control frameworks:")
        for fw in fws:
            ctrls = get_framework(fw)
            print(f"  {fw:<12} ({len(ctrls)} controls)")
        print()

    elif args.command == "scan":
        if args.demo:
            _run_demo(args)
        elif args.file:
            _run_file_scan(args)
        else:
            print("Error: --file or --demo is required for scan command.")
            sys.exit(1)

    else:
        parser.print_help()


def _run_demo(args) -> None:
    """Run the coverage mapper against the built-in demo policy."""
    demo_text = get_demo_policy_text()
    demo_path = Path("/tmp/demo-policy.md")
    demo_path.write_text(demo_text)

    try:
        parsed = parse_policy_document(str(demo_path))
    finally:
        demo_path.unlink(missing_ok=True)

    print(f"\n  Parsed demo policy: {len(parsed.paragraphs)} paragraphs, "
          f"{len(parsed.extracted_controls)} extracted control statements")

    _run_mapping(parsed, args)


def _run_file_scan(args) -> None:
    """Run the coverage mapper against a user-provided file."""
    filepath = str(args.file.resolve())
    parsed = parse_policy_document(filepath)
    print(f"\n  Parsed '{filepath}': {len(parsed.paragraphs)} paragraphs, "
          f"{len(parsed.extracted_controls)} extracted control statements")
    _run_mapping(parsed, args)


def _run_mapping(parsed, args) -> None:
    """Map extracted controls against selected framework(s)."""
    framework_map = {
        "iso27001": "ISO27001",
        "nist_csf": "NIST_CSF",
        "cis_v8": "CIS_V8",
        "vodafone": "VODAFONE",
    }

    if args.framework == "all":
        fw_keys = list(framework_map.values())
    else:
        fw_keys = [framework_map[args.framework]]

    results = []
    for fw_key in fw_keys:
        fw_controls = get_framework(fw_key)
        result = map_coverage(parsed.extracted_controls, fw_controls)
        results.append(result)

    print_summary(results)

    json_path = save_json_report(results, str(args.output))
    print(f"  JSON report saved to: {json_path}")

    if args.csv:
        csv_path = save_csv_report(results, str(args.csv))
        print(f"  CSV report saved to:   {csv_path}")

    # Summarise total gaps
    for r in results:
        if r.gaps_list:
            print(f"\n  Action items for {r.framework}:")
            for g in r.gaps_list:
                from .mapper import generate_remediation
                remedy = generate_remediation(g.category)
                print(f"    - Add coverage for [{g.control_id}] {g.title} ({g.category})")
                print(f"      {remedy}")


if __name__ == "__main__":
    main()

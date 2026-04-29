"""CLI for IAM Access Lifecycle Simulator."""

import argparse
import sys
import json
from pathlib import Path

from .models import ADUser, HREmployee, ITSMTicket
from .engine import run_all_checks
from .reporter import build_audit_report, export_json


def main():
    parser = argparse.ArgumentParser(
        prog="access-lifecycle",
        description="IAM Access Lifecycle Simulator -- audit AD, HR, and ITSM data for access violations",
    )
    sub = parser.add_subparsers(dest="command")

    scan_p = sub.add_parser("scan", help="Run access lifecycle audit")
    scan_p.add_argument("--ad-file", type=Path, help="Path to AD export CSV")
    scan_p.add_argument("--hr-file", type=Path, help="Path to HR export CSV")
    scan_p.add_argument("--itsm-file", type=Path, help="Path to ITSM log CSV")
    scan_p.add_argument("--output", "-o", type=Path, default=Path("data/audit-report.json"),
                        help="Output path for JSON report")
    scan_p.add_argument("--demo", action="store_true",
                        help="Run against built-in demo data")
    scan_p.add_argument("--cert-report", action="store_true",
                        help="Include access certification output in report")

    args = parser.parse_args()

    if args.command == "scan":
        if args.demo:
            from .data import load_sample_data
            ad_users, hr_employees, itsm_tickets = load_sample_data()
        elif args.ad_file and args.hr_file:
            ad_users = _load_ad_csv(args.ad_file)
            hr_employees = _load_hr_csv(args.hr_file)
            itsm_tickets = []
            if args.itsm_file:
                itsm_tickets = _load_itsm_csv(args.itsm_file)
        else:
            print("Error: --ad-file and --hr-file required, or use --demo")
            sys.exit(1)

        violations = run_all_checks(ad_users, hr_employees, itsm_tickets)
        report = build_audit_report(
            violations,
            ad_count=len(ad_users),
            hr_count=len(hr_employees),
            itsm_count=len(itsm_tickets),
        )

        path = export_json(report, args.output)
        _print_summary(report)
        if args.cert_report:
            _print_certification(report)
        print(f"\nReport saved to {path.resolve()}")

    else:
        parser.print_help()


def _print_summary(report):
    s = report.summary
    by_sev = s["by_severity"]
    by_type = s["by_type"]

    print(f"\n{'='*60}")
    print(f"  IAM Access Lifecycle Audit Complete")
    print(f"{'='*60}")
    print(f"  Scope:     {report.scope}")
    print(f"  Violations: {s['total']} total")
    print(f"    CRITICAL: {by_sev['CRITICAL']}")
    print(f"    HIGH:     {by_sev['HIGH']}")
    print(f"    MEDIUM:   {by_sev['MEDIUM']}")
    print()
    print(f"  By Type:")
    for vtype, count in sorted(by_type.items()):
        print(f"    {vtype:<20} {count}")
    print(f"{'='*60}")


def _print_certification(report):
    print(f"\n{'='*60}")
    print(f"  Access Certification Items")
    print(f"{'='*60}")
    for item in report.access_certification_items:
        print(f"  [{item['action']:<7}] {item['type']:<18} "
              f"{item['affected_accounts'][0] if item['affected_accounts'] else 'N/A'}")
        print(f"         Certify by: {item['certify_by'][:19]}")
        print(f"         Control: {item['control_id']}")
    print(f"{'='*60}")


def _load_ad_csv(path: Path) -> list[ADUser]:
    import csv
    users = []
    with open(path) as f:
        for row in csv.DictReader(f):
            from datetime import datetime
            ll = row.get("LastLogon")
            users.append(ADUser(
                SamAccountName=row["SamAccountName"],
                EmployeeID=row["EmployeeID"],
                Enabled=row.get("Enabled", "True").lower() in ("true", "1", "yes"),
                LastLogon=datetime.fromisoformat(ll) if ll else None,
                MFAEnabled=row.get("MFAEnabled", "False").lower() in ("true", "1", "yes"),
                Group=row.get("Group", "Domain Users"),
                ManagerDN=row.get("ManagerDN", ""),
            ))
    return users


def _load_hr_csv(path: Path) -> list[HREmployee]:
    import csv
    employees = []
    with open(path) as f:
        for row in csv.DictReader(f):
            from datetime import datetime
            td = row.get("TerminationDate")
            employees.append(HREmployee(
                EmployeeID=row["EmployeeID"],
                Status=row.get("Status", "Active"),
                Department=row.get("Department", ""),
                ManagerID=row.get("ManagerID", ""),
                TerminationDate=datetime.fromisoformat(td) if td else None,
            ))
    return employees


def _load_itsm_csv(path: Path) -> list[ITSMTicket]:
    import csv
    tickets = []
    with open(path) as f:
        for row in csv.DictReader(f):
            from datetime import datetime
            cd = row.get("CreatedDate")
            tickets.append(ITSMTicket(
                TicketID=row["TicketID"],
                RequestorID=row["RequestorID"],
                ApproverID=row["ApproverID"],
                ChangeType=row.get("ChangeType", "Access Request"),
                CreatedDate=datetime.fromisoformat(cd) if cd else None,
            ))
    return tickets


if __name__ == "__main__":
    main()

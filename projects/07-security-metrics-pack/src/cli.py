"""CLI for Security Metrics Pack."""

import argparse
import sys
import json
from pathlib import Path

from .models import IncidentRecord, AlertRecord, VulnerabilityRecord, MetricSeverity
from .scanner import compute
from .reporter import export_json


def main():
    parser = argparse.ArgumentParser(
        prog="security-metrics",
        description="Security Metrics Pack — MTTD/MTTR, alert quality, vuln SLA tracking",
    )
    sub = parser.add_subparsers(dest="command")

    compute_p = sub.add_parser("compute", help="Compute metrics from input data")
    compute_p.add_argument("--incidents", "-i", type=Path, help="JSON file with incident records")
    compute_p.add_argument("--alerts", "-a", type=Path, help="JSON file with alert records")
    compute_p.add_argument("--vulns", "-v", type=Path, help="JSON file with vulnerability records")
    compute_p.add_argument("--output", "-o", type=Path, default=Path("metrics-report.json"))
    compute_p.add_argument("--charts", "-c", action="store_true", help="Generate PNG charts")
    compute_p.add_argument("--chart-dir", type=Path, default=Path("data/charts"))
    compute_p.add_argument("--demo", action="store_true", help="Run against built-in demo data")
    compute_p.add_argument("--period-start", default="", help="Reporting period start")
    compute_p.add_argument("--period-end", default="", help="Reporting period end")

    args = parser.parse_args()

    if args.command == "compute":
        if args.demo:
            incidents = _demo_incidents()
            alerts = _demo_alerts()
            vulns = _demo_vulns()
        else:
            incidents = _load(args.incidents, IncidentRecord) if args.incidents else None
            alerts = _load(args.alerts, AlertRecord) if args.alerts else None
            vulns = _load(args.vulns, VulnerabilityRecord) if args.vulns else None

        if not any([incidents, alerts, vulns]):
            print("Error: at least one of --incidents, --alerts, --vulns required (or --demo)")
            sys.exit(1)

        report = compute(incidents, alerts, vulns, args.period_start, args.period_end)
        path = export_json(report, args.output)
        _print_summary(report)
        print(f"\nReport saved to {path}")

        if args.charts:
            try:
                from .charts import export_charts
                chart_paths = export_charts(report, args.chart_dir)
                for cp in chart_paths:
                    print(f"Chart saved to {cp}")
            except ImportError:
                print("Warning: matplotlib not installed. JSON report saved; charts skipped.")
                print("Install with: pip install matplotlib")

    else:
        parser.print_help()


def _print_summary(report):
    print(f"\n{'='*60}")
    print(f"  Security Metrics Report")
    print(f"{'='*60}")
    print(f"  RAG Status:               {report.rag_status()}")
    print(f"  MTTD:                     {report.mttd_mttr.mttd_hours}h")
    print(f"  MTTR (Respond):           {report.mttd_mttr.mttr_hours}h")
    print(f"  MTTR (Resolve):           {report.mttd_mttr.mtt_resolve_hours}h")
    print(f"  Alert Precision:          {report.alert_quality.precision_pct}%")
    print(f"  False Positive Rate:      {report.alert_quality.false_positive_rate_pct}%")
    print(f"  Vuln SLA Compliance:      {report.vuln_sla.sla_compliance_pct}%")
    print(f"  Critical Vuln Breaches:   {report.vuln_sla.critical_breached}")
    print(f"  Overdue Critical Vulns:   {report.vuln_sla.overdue_critical}")
    print(f"{'='*60}")


def _load(path: Path, cls):
    data = json.loads(path.read_text())
    return [cls(**item) for item in data]


def _demo_incidents():
    return [
        IncidentRecord("INC-001", "2026-04-01T09:00:00", "2026-04-01T09:45:00",
                       "2026-04-02T14:00:00", MetricSeverity.HIGH, "SIEM"),
        IncidentRecord("INC-002", "2026-04-03T11:00:00", "2026-04-03T11:30:00",
                       "2026-04-04T10:00:00", MetricSeverity.MEDIUM, "EDR"),
        IncidentRecord("INC-003", "2026-04-05T08:00:00", "2026-04-05T09:00:00",
                       "2026-04-05T20:00:00", MetricSeverity.CRITICAL, "SOC"),
        IncidentRecord("INC-004", "2026-04-08T14:00:00", "2026-04-08T16:00:00",
                       "2026-04-10T12:00:00", MetricSeverity.HIGH, "SIEM"),
        IncidentRecord("INC-005", "2026-04-12T03:00:00", None, None, MetricSeverity.CRITICAL, "SOC"),
        IncidentRecord("INC-006", "2026-04-15T10:00:00", "2026-04-15T11:00:00",
                       "2026-04-16T09:00:00", MetricSeverity.LOW, "EDR"),
    ]


def _demo_alerts():
    return [
        AlertRecord("ALT-001", "2026-04-01T09:00:00", True, False, MetricSeverity.HIGH, "SIEM", "Brute Force"),
        AlertRecord("ALT-002", "2026-04-01T10:00:00", False, True, MetricSeverity.MEDIUM, "SIEM", "False Positive"),
        AlertRecord("ALT-003", "2026-04-02T08:00:00", True, False, MetricSeverity.CRITICAL, "EDR", "Ransomware"),
        AlertRecord("ALT-004", "2026-04-03T14:00:00", True, False, MetricSeverity.HIGH, "SOC", "Data Exfil"),
        AlertRecord("ALT-005", "2026-04-04T06:00:00", False, True, MetricSeverity.LOW, "SIEM", "Benign Scan"),
        AlertRecord("ALT-006", "2026-04-05T12:00:00", True, False, MetricSeverity.MEDIUM, "EDR", "Suspicious Process"),
        AlertRecord("ALT-007", "2026-04-06T09:00:00", True, False, MetricSeverity.HIGH, "SOC", "Priv Escalation"),
        AlertRecord("ALT-008", "2026-04-07T16:00:00", False, True, MetricSeverity.LOW, "SIEM", "Noise"),
        AlertRecord("ALT-009", "2026-04-08T11:00:00", True, False, MetricSeverity.CRITICAL, "EDR", "C2 Beacon"),
        AlertRecord("ALT-010", "2026-04-09T07:00:00", True, False, MetricSeverity.MEDIUM, "SOC", "Phishing"),
    ]


def _demo_vulns():
    return [
        VulnerabilityRecord("VULN-001", "2026-03-01T00:00:00", MetricSeverity.CRITICAL, 9.8,
                           "2026-03-15T00:00:00", 14, "web-server-01"),
        VulnerabilityRecord("VULN-002", "2026-03-05T00:00:00", MetricSeverity.HIGH, 7.5,
                           "2026-04-01T00:00:00", 30, "db-server-01"),
        VulnerabilityRecord("VULN-003", "2026-03-10T00:00:00", MetricSeverity.MEDIUM, 5.0,
                           "2026-03-20T00:00:00", 30, "app-server-02"),
        VulnerabilityRecord("VULN-004", "2026-04-01T00:00:00", MetricSeverity.CRITICAL, 9.0,
                           None, 14, "web-server-02"),
        VulnerabilityRecord("VULN-005", "2026-04-02T00:00:00", MetricSeverity.HIGH, 8.1,
                           "2026-04-20T00:00:00", 30, "db-server-02"),
        VulnerabilityRecord("VULN-006", "2026-04-05T00:00:00", MetricSeverity.CRITICAL, 9.5,
                           None, 14, "web-server-01"),
        VulnerabilityRecord("VULN-007", "2026-04-10T00:00:00", MetricSeverity.MEDIUM, 4.5,
                           "2026-04-28T00:00:00", 30, "app-server-01"),
        VulnerabilityRecord("VULN-008", "2026-04-15T00:00:00", MetricSeverity.LOW, 2.0,
                           "2026-04-25T00:00:00", 90, "monitoring-01"),
    ]


if __name__ == "__main__":
    main()

"""CLI for Risk Register + Scoring Engine."""

import argparse
import sys
from datetime import date
from pathlib import Path

from .models import (
    RiskRegister, RiskCategory, RiskStatus, RiskLevel,
    SSVCMetric, SSVCDecision, Exploitation, Automatable, TechnicalImpact, MissionImpact,
)
from .register import (
    create_risk, add_to_register, update_risk, accept_risk,
    mitigate_risk, close_risk, filter_by_status, filter_by_category,
    filter_by_level, get_overdue_reviews, get_risk_matrix,
)
from .reporter import (
    print_risk_matrix, print_risk_summary, print_risk_detail,
    save_register_json, save_register_csv,
)
from .demo_data import build_demo_register


def _build_list_table(risks) -> str:
    """Build an ASCII table of risks."""
    if not risks:
        return "\n  No risks found.\n"

    lines = []
    lines.append("")
    lines.append(f"  {'ID':<10} {'Level':<10} {'CVSS':>6} {'SSVC':<10} {'Status':<12} {'Category':<16} Title")
    lines.append("  " + "-" * 100)
    for r in risks:
        lines.append(
            f"  {r.risk_id:<10} {r.risk_level.value:<10} {r.cvss_score:>5.1f}  "
            f"{r.ssvc_decision.value:<10} {r.status.value:<12} {r.category.value:<16} {r.title[:40]}"
        )
    lines.append("  " + "-" * 100)
    lines.append(f"  {len(risks)} risk(s) listed.")
    lines.append("")
    return "\n".join(lines)


def _parse_category(value: str) -> RiskCategory:
    try:
        return RiskCategory[value.upper()]
    except KeyError:
        valid = [c.value for c in RiskCategory]
        raise argparse.ArgumentTypeError(f"Invalid category. Choose from: {valid}")


def _parse_status(value: str) -> RiskStatus:
    try:
        return RiskStatus[value.upper()]
    except KeyError:
        valid = [s.value for s in RiskStatus]
        raise argparse.ArgumentTypeError(f"Invalid status. Choose from: {valid}")


def _parse_level(value: str) -> RiskLevel:
    try:
        return RiskLevel[value.upper()]
    except KeyError:
        valid = [lv.value for lv in RiskLevel]
        raise argparse.ArgumentTypeError(f"Invalid level. Choose from: {valid}")


def _parse_exploitation(value: str) -> Exploitation:
    try:
        return Exploitation[value.upper()]
    except KeyError:
        raise argparse.ArgumentTypeError("Choose from: NONE, POC, ACTIVE")


def _parse_automatable(value: str) -> Automatable:
    try:
        return Automatable[value.upper()]
    except KeyError:
        raise argparse.ArgumentTypeError("Choose from: YES, NO")


def _parse_tech_impact(value: str) -> TechnicalImpact:
    try:
        return TechnicalImpact[value.upper()]
    except KeyError:
        raise argparse.ArgumentTypeError("Choose from: PARTIAL, TOTAL")


def _parse_mission_impact(value: str) -> MissionImpact:
    try:
        return MissionImpact[value.upper()]
    except KeyError:
        raise argparse.ArgumentTypeError("Choose from: LOW, MEDIUM, HIGH")


def _load_register(path: Path) -> RiskRegister:
    """Load a register from JSON, or return a new one if file doesn't exist."""
    import json
    if path.exists():
        data = json.loads(path.read_text())
        reg = RiskRegister(
            owner=data.get("metadata", {}).get("owner", ""),
            created=data.get("metadata", {}).get("created", ""),
            updated=data.get("metadata", {}).get("updated", ""),
        )
        for rdict in data.get("risks", []):
            from .models import Risk
            risk = Risk(
                risk_id=rdict["risk_id"],
                title=rdict["title"],
                description=rdict.get("description", ""),
                category=RiskCategory[rdict["category"]],
                owner=rdict.get("owner", ""),
                identified_date=date.fromisoformat(rdict["identified_date"]),
                status=RiskStatus[rdict["status"]],
                cvss_score=rdict["cvss_score"],
                cvss_vector=rdict.get("cvss_vector", ""),
                ssvc_decision=SSVCDecision(rdict["ssvc_decision"]),
                impact_score=rdict.get("impact_score", 50),
                likelihood_score=rdict.get("likelihood_score", 50),
                risk_level=RiskLevel[rdict["risk_level"]],
                acceptance_rationale=rdict.get("acceptance_rationale"),
                treatment_plan=rdict.get("treatment_plan", ""),
                review_date=date.fromisoformat(rdict["review_date"]) if rdict.get("review_date") else None,
                control_mapping=rdict.get("control_mapping", []),
            )
            reg.add(risk)
        return reg
    return RiskRegister()


def _save_register(register: RiskRegister, path: Path) -> None:
    save_register_json(register, path)


def main():
    parser = argparse.ArgumentParser(
        prog="risk-register",
        description="Risk Register + Scoring Engine — CVSS v3.1 / SSVC v2 risk management",
    )
    sub = parser.add_subparsers(dest="command")

    # -- list --
    list_p = sub.add_parser("list", help="List risks in the register")
    list_p.add_argument("--status", type=_parse_status, help="Filter by status")
    list_p.add_argument("--category", type=_parse_category, help="Filter by category")
    list_p.add_argument("--level", type=_parse_level, help="Filter by risk level")
    list_p.add_argument("--file", "-f", type=Path, default=Path("data/risk-register.json"),
                        help="Register file path")

    # -- create --
    create_p = sub.add_parser("create", help="Create a new risk")
    create_p.add_argument("--title", required=True, help="Risk title")
    create_p.add_argument("--description", default="", help="Risk description")
    create_p.add_argument("--category", type=_parse_category, required=True, help="Risk category")
    create_p.add_argument("--cvss-vector", default="AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
                          help="CVSS v3.1 vector string")
    create_p.add_argument("--exploitation", type=_parse_exploitation, default="POC",
                          help="SSVC exploitation state")
    create_p.add_argument("--automatable", type=_parse_automatable, default="YES",
                          help="SSVC automatable")
    create_p.add_argument("--tech-impact", type=_parse_tech_impact, default="TOTAL",
                          dest="tech_impact", help="SSVC technical impact")
    create_p.add_argument("--mission-impact", type=_parse_mission_impact, default="MEDIUM",
                          dest="mission_impact", help="SSVC mission impact")
    create_p.add_argument("--owner", default="", help="Risk owner")
    create_p.add_argument("--impact", type=int, default=50, help="Impact score 0-100")
    create_p.add_argument("--likelihood", type=int, default=50, help="Likelihood score 0-100")
    create_p.add_argument("--treatment", default="", help="Treatment plan")
    create_p.add_argument("--controls", default="", help="Comma-separated control IDs")
    create_p.add_argument("--file", "-f", type=Path, default=Path("data/risk-register.json"),
                          help="Register file path")

    # -- view --
    view_p = sub.add_parser("view", help="View full risk detail")
    view_p.add_argument("--risk-id", required=True, help="Risk ID (e.g. RSK-001)")
    view_p.add_argument("--file", "-f", type=Path, default=Path("data/risk-register.json"),
                        help="Register file path")

    # -- accept --
    accept_p = sub.add_parser("accept", help="Accept a risk")
    accept_p.add_argument("--risk-id", required=True, help="Risk ID")
    accept_p.add_argument("--rationale", required=True, help="Acceptance rationale")
    accept_p.add_argument("--accepted-by", default="", help="Who accepted the risk")
    accept_p.add_argument("--review-days", type=int, default=90, help="Days until review")
    accept_p.add_argument("--file", "-f", type=Path, default=Path("data/risk-register.json"),
                          help="Register file path")

    # -- matrix --
    matrix_p = sub.add_parser("matrix", help="Print the 5x5 risk matrix")
    matrix_p.add_argument("--file", "-f", type=Path, default=Path("data/risk-register.json"),
                          help="Register file path")

    # -- export --
    export_p = sub.add_parser("export", help="Export register to JSON or CSV")
    export_p.add_argument("--format", "-fmt", choices=["json", "csv"], default="json",
                          help="Export format")
    export_p.add_argument("--output", "-o", type=Path, required=True, help="Output file path")
    export_p.add_argument("--file", "-f", type=Path, default=Path("data/risk-register.json"),
                          help="Register file path")

    # -- demo --
    demo_p = sub.add_parser("demo", help="Load demo data and display matrix + summary + export")
    demo_p.add_argument("--output", "-o", type=Path, default=Path("data/demo-risk-register.json"),
                        help="Export path for demo register")

    args = parser.parse_args()

    if args.command == "demo":
        register = build_demo_register()
        print_risk_summary(register)
        print_risk_matrix(register)
        path = save_register_json(register, args.output)
        print(f"  Demo register exported to {path}")
        overdue = get_overdue_reviews(register)
        if overdue:
            print(f"\n  Overdue reviews: {len(overdue)}")
            for r in overdue:
                print(f"    - {r.risk_id}: {r.title} (review was {r.review_date})")
        return

    if args.command == "list":
        register = _load_register(args.file)
        risks = register.risks
        if args.status:
            risks = filter_by_status(register, args.status)
        if args.category:
            risks = filter_by_category(register, args.category)
        if args.level:
            risks = filter_by_level(register, args.level)
        print(_build_list_table(risks))
        return

    if args.command == "create":
        register = _load_register(args.file)
        ssvc_metric = SSVCMetric(
            exploitation=args.exploitation,
            automatable=args.automatable,
            technical_impact=args.tech_impact,
            mission_impact=args.mission_impact,
        )
        controls = [c.strip() for c in args.controls.split(",") if c.strip()] if args.controls else []
        risk = create_risk(
            title=args.title,
            description=args.description,
            category=args.category,
            cvss_vector=args.cvss_vector,
            ssvc_metric=ssvc_metric,
            owner=args.owner,
            impact_score=args.impact,
            likelihood_score=args.likelihood,
            treatment_plan=args.treatment,
            control_mapping=controls,
        )
        risk = add_to_register(register, risk)
        _save_register(register, args.file)
        print(f"\n  Risk created: {risk.risk_id} — {risk.title}")
        print(f"  CVSS Score: {risk.cvss_score}  |  SSVC: {risk.ssvc_decision.value}  |  Level: {risk.risk_level.value}")
        return

    if args.command == "view":
        register = _load_register(args.file)
        risk = register.get(args.risk_id)
        if risk is None:
            print(f"  Risk '{args.risk_id}' not found.")
            sys.exit(1)
        print_risk_detail(risk)
        return

    if args.command == "accept":
        register = _load_register(args.file)
        risk = register.get(args.risk_id)
        if risk is None:
            print(f"  Risk '{args.risk_id}' not found.")
            sys.exit(1)
        accept_risk(risk, args.rationale, args.accepted_by or risk.owner, args.review_days)
        _save_register(register, args.file)
        print(f"  Risk {risk.risk_id} accepted. Review due: {risk.review_date}")
        return

    if args.command == "matrix":
        register = _load_register(args.file)
        print_risk_matrix(register)
        return

    if args.command == "export":
        register = _load_register(args.file)
        if args.format == "csv":
            path = save_register_csv(register, args.output)
        else:
            path = save_register_json(register, args.output)
        print(f"  Register exported to {path} ({len(register.risks)} risks)")
        return

    parser.print_help()


if __name__ == "__main__":
    main()

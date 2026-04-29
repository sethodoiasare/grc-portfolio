"""CLI for Incident Response Runbook Generator."""

import argparse
import sys
import json
from pathlib import Path

from .models import INCIDENT_TYPE_LABELS
from .templates import TEMPLATES
from .demo_context import get_demo_context
from .generator import generate_runbook, generate_all, save_runbook


def main():
    parser = argparse.ArgumentParser(
        prog="ir-runbook",
        description="Incident Response Runbook Generator -- battle-tested IR templates with AI-assisted customisation",
    )
    sub = parser.add_subparsers(dest="command")

    # generate
    gen_p = sub.add_parser("generate", help="Generate incident response runbooks")
    gen_p.add_argument(
        "--type", "-t",
        choices=["malware", "ransomware", "breach", "ddos", "insider", "credential", "all"],
        default="ransomware",
        help="Incident type (default: ransomware)",
    )
    gen_p.add_argument(
        "--context-file", "-c",
        type=Path,
        help="JSON file with organisation context",
    )
    gen_p.add_argument(
        "--severity", "-s",
        choices=["SEV1", "SEV2", "SEV3"],
        default="SEV2",
        help="Incident severity (default: SEV2)",
    )
    gen_p.add_argument(
        "--output-dir", "-o",
        type=Path,
        default=Path("data"),
        help="Output directory for runbook files (default: data/)",
    )
    gen_p.add_argument(
        "--format", "-f",
        choices=["md", "json", "pdf", "all"],
        default="md",
        help="Output format (default: md)",
    )
    gen_p.add_argument(
        "--demo",
        action="store_true",
        help="Generate demo runbooks for PayFlow Ltd fintech context",
    )

    # list-templates
    list_p = sub.add_parser("list-templates", help="List available incident type templates")

    args = parser.parse_args()

    if args.command == "generate":
        if args.demo:
            _run_demo(args)
        else:
            _run_generate(args)

    elif args.command == "list-templates":
        _list_templates()

    else:
        parser.print_help()


def _run_demo(args):
    """Generate 2 demo runbooks for PayFlow Ltd."""
    context = get_demo_context()
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate ransomware SEV2 and data breach SEV1
    configs = [
        ("ransomware", "SEV2"),
        ("breach", "SEV1"),
    ]

    saved_all: list[Path] = []
    for incident_type, severity in configs:
        runbook = generate_runbook(incident_type, severity, context)
        saved = save_runbook(runbook, output_dir, format=args.format)
        saved_all.extend(saved)

        label = INCIDENT_TYPE_LABELS.get(incident_type, incident_type)
        print(f"\n{'='*60}")
        print(f"  {label} -- {severity}")
        print(f"  Organisation: {runbook.organization}")
        print(f"{'='*60}")
        print(f"  Total Stages:  {len(runbook.stages)}")
        print(f"  Total Actions: {runbook.total_actions}")
        print(f"  RTO:           {runbook.recovery_objectives.get('rto_hours', 'N/A')} hours")
        print(f"  RPO:           {runbook.recovery_objectives.get('rpo_hours', 'N/A')} hours")
        print(f"  Contacts:      {len(runbook.contacts)}")
        print(f"  Tools:         {len(runbook.tools)}")
        print(f"  Comms Items:   {len(runbook.communication_plan)}")
        print()

        # Print stage summary
        for stage in runbook.stages:
            print(f"  Stage {stage.stage_number}: {stage.stage_name:30s}  {len(stage.actions):2d} actions  SLA: {stage.sla_minutes:5d} min")

    print(f"\n{'='*60}")
    print(f"  Demo complete. {len(saved_all)} files saved to {output_dir}")
    for s in saved_all:
        print(f"    {s}")
    print(f"{'='*60}")


def _run_generate(args):
    """Generate runbooks from command line arguments."""
    # Load context
    context = {}
    if args.context_file:
        if not args.context_file.exists():
            print(f"Error: context file not found: {args.context_file}", file=sys.stderr)
            sys.exit(1)
        context = json.loads(args.context_file.read_text())

    incident_types = list(TEMPLATES.keys()) if args.type == "all" else [args.type]

    output_dir = args.output_dir
    saved_all: list[Path] = []

    for incident_type in incident_types:
        runbook = generate_runbook(incident_type, args.severity, context)
        saved = save_runbook(runbook, output_dir, format=args.format)
        saved_all.extend(saved)

        label = INCIDENT_TYPE_LABELS.get(incident_type, incident_type)
        print(f"Generated: {label} ({args.severity}) -- {len(runbook.stages)} stages, {runbook.total_actions} actions")

    print(f"\n{len(saved_all)} file(s) saved to {output_dir.resolve()}")


def _list_templates():
    """Print available templates with descriptions."""
    descriptions = {
        "malware": "Virus/worm/trojan outbreak -- detection, containment, eradication, recovery",
        "ransomware": "Ransomware encryption attack -- network isolation, backup protection, negotiation/decryption workflow",
        "breach": "Unauthorised data access/exfiltration -- DLP, regulatory notification (GDPR, PCI-DSS), dark web monitoring",
        "ddos": "Distributed denial-of-service -- CDN scrubbing, rate limiting, ISP coordination, capacity planning",
        "insider": "Malicious or negligent insider -- UEBA, HR/Legal coordination, evidence preservation, access review",
        "credential": "Compromised credentials/theft -- session revocation, MFA enforcement, credential rotation, persistence hunting",
    }

    print(f"\n{'Incident Type':<15} {'Stages':<8} Description")
    print("-" * 80)
    for incident_type in ["malware", "ransomware", "breach", "ddos", "insider", "credential"]:
        template = TEMPLATES.get(incident_type)
        stages = len(template.base_stages) if template else 0
        desc = descriptions.get(incident_type, "")
        print(f"{incident_type:<15} {stages:<8} {desc}")
    print(f"\n{len(TEMPLATES)} templates available.")
    print("Use 'generate --type <type> --demo' to generate a sample runbook.")


if __name__ == "__main__":
    main()

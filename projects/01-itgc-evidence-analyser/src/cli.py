"""
CLI Entry Point

Full Click CLI for the AI ITGC Evidence Analyser. Provides four commands:

  assess        — assess a single control against a file of evidence
  batch         — run multiple assessments from a YAML config file
  list-controls — list / filter / search available Vodafone ITGC controls
  summary       — print an executive summary panel from an existing JSON report
"""

import click
import json
import sys
import yaml
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

# Load .env from project root or CWD if present
try:
    from dotenv import load_dotenv
    for _p in [Path(__file__).parents[3] / ".env", Path.cwd() / ".env"]:
        if _p.exists():
            load_dotenv(_p)
            break
except ImportError:
    pass

from src.assessor import EvidenceAssessor
from src.control_parser import ControlParser
from src.report_generator import ReportGenerator

console = Console()


@click.group()
def cli():
    """AI ITGC Evidence Analyser — Vodafone Control Assessment Engine

    Assess audit evidence against Vodafone cybersecurity controls using Claude AI.
    Maps findings to D/E statement requirements and generates professional reports.
    """
    pass


@cli.command()
@click.option("--control", "-c", required=True, help="Control ID e.g. IAM_001, VUL_001")
@click.option("--evidence", "-e", required=True, type=click.Path(), help="Path to evidence file (.txt, .pdf, .csv)")
@click.option("--statement-type", "-s", default="D", type=click.Choice(["D", "E"]), show_default=True)
@click.option("--output", "-o", default=None, help="Output JSON file path (default: stdout)")
@click.option("--pdf", is_flag=True, help="Also generate a PDF report alongside the JSON output")
def assess(control, evidence, statement_type, output, pdf):
    """Assess a single control against audit evidence."""
    assessor = EvidenceAssessor()
    generator = ReportGenerator()

    with console.status(f"[bold cyan]Assessing {control} against {evidence}..."):
        result = assessor.assess_from_file(control, evidence, statement_type)

    generator.generate_summary_table([result])

    report = generator.generate_json_report(
        [result], audit_scope=f"Single control assessment: {control}"
    )

    if output:
        out_path = Path(output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, indent=2))
        console.print(f"[green]JSON report saved to {output}[/green]")
        if pdf:
            pdf_path = str(out_path.with_suffix(".pdf"))
            generator.generate_pdf_report(
                [result],
                audit_scope=f"Single control assessment: {control}",
                output_path=pdf_path,
            )
            console.print(f"[green]PDF report saved to {pdf_path}[/green]")
    else:
        click.echo(json.dumps(report, indent=2))


@cli.command()
@click.option("--config", "-c", required=True, type=click.Path(exists=True), help="YAML batch config file")
@click.option("--output-dir", "-o", default="./reports", show_default=True, help="Output directory for reports")
@click.option("--format", "fmt", type=click.Choice(["json", "pdf", "both"]), default="both", show_default=True)
def batch(config, output_dir, fmt):
    """Run batch assessment from a YAML config file.

    Config format:
    \b
    audit_scope: "Vodafone UK ITGC Q1 2026"
    assessments:
      - control_id: IAM_001
        evidence_file: data/samples/sample_evidence_iam001.txt
        statement_type: D
    """
    config_data = yaml.safe_load(Path(config).read_text())
    audit_scope = config_data.get("audit_scope", "Batch Assessment")
    items = config_data.get("assessments", [])

    if not items:
        console.print("[red]No assessments found in config file.[/red]")
        sys.exit(1)

    assessor = EvidenceAssessor()
    generator = ReportGenerator()
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    results = []
    with console.status("[bold cyan]Running batch assessment...") as status:
        for i, item in enumerate(items, 1):
            control_id = item["control_id"]
            evidence_file = item["evidence_file"]
            stmt_type = item.get("statement_type", "D")
            status.update(f"[bold cyan]Assessing {control_id} ({i}/{len(items)})...")
            result = assessor.assess_from_file(control_id, evidence_file, stmt_type)
            results.append(result)

    generator.generate_summary_table(results)

    report = generator.generate_json_report(results, audit_scope)

    if fmt in ("json", "both"):
        json_file = out_path / "assessment_report.json"
        json_file.write_text(json.dumps(report, indent=2))
        console.print(f"[green]JSON report: {json_file}[/green]")

    if fmt in ("pdf", "both"):
        pdf_file = str(out_path / "assessment_report.pdf")
        generator.generate_pdf_report(results, audit_scope, pdf_file)
        console.print(f"[green]PDF report: {pdf_file}[/green]")


@cli.command("list-controls")
@click.option("--domain", "-d", default=None, help="Filter by domain (IAM, CHG, INC, BCK, VUL)")
@click.option("--search", "-q", default=None, help="Search controls by keyword")
def list_controls(domain, search):
    """List all available Vodafone ITGC controls."""
    from rich.table import Table
    from rich import box

    parser = ControlParser()

    if search:
        controls = parser.search(search)
    elif domain:
        controls = parser.get_by_domain(domain.upper())
    else:
        controls = parser.list_controls()

    table = Table(title="Available ITGC Controls", box=box.ROUNDED)
    table.add_column("Control ID", style="bold cyan", no_wrap=True)
    table.add_column("Control Name")
    table.add_column("Domain", no_wrap=True)
    table.add_column("Standard", no_wrap=True)
    table.add_column("D Stmts", justify="right")
    table.add_column("E Stmts", justify="right")

    for c in controls:
        table.add_row(
            c["control_id"],
            c["control_name"],
            c["domain"],
            c["vodafone_standard"],
            str(len(c["d_statements"])),
            str(len(c["e_statements"])),
        )

    console_inner = Console()
    console_inner.print(table)
    console_inner.print(f"\n  {len(controls)} control(s) shown.\n")


@cli.command()
@click.argument("report_file", type=click.Path(exists=True))
def summary(report_file):
    """Print executive summary from an existing JSON report."""
    from rich.table import Table
    from rich import box

    console_inner = Console()
    data = json.loads(Path(report_file).read_text())
    s = data.get("summary", {})

    rag = s.get("rag_status", "UNKNOWN")
    rag_colour = {"GREEN": "green", "AMBER": "yellow", "RED": "red"}.get(rag, "white")

    panel_text = (
        f"Audit Scope: [bold]{data.get('audit_scope', 'N/A')}[/bold]\n"
        f"Generated:   {data.get('generated_at', 'N/A')}\n\n"
        f"Controls assessed: {s.get('total_controls_assessed', 0)}\n"
        f"  Passed:            {s.get('pass', 0)}\n"
        f"  Partial:           {s.get('partial', 0)}\n"
        f"  Failed:            {s.get('fail', 0)}\n"
        f"  Insufficient:      {s.get('insufficient_evidence', 0)}\n\n"
        f"Pass rate:    {s.get('pass_rate_pct', 0)}%\n"
        f"RAG Status:   [{rag_colour}][bold]{rag}[/bold][/{rag_colour}]\n"
        f"Tokens used:  {s.get('total_tokens_used', 0):,}"
    )

    console_inner.print(
        Panel(panel_text, title="ITGC Assessment Summary", border_style=rag_colour)
    )

    findings = data.get("findings", [])
    if findings:
        console_inner.print(
            f"\n  [bold red]{len(findings)} finding(s) requiring attention:[/bold red]"
        )
        for f in findings:
            df = f.get("draft_finding") or {}
            console_inner.print(
                f"  - [{f['verdict']}] {f['control_id']} -- {df.get('title', 'No title')}"
            )


if __name__ == "__main__":
    cli()

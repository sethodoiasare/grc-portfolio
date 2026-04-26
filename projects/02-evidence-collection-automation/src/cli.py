"""CLI entry point for the Evidence Collection Automator."""

import json
import sys

import click
from rich.console import Console
from rich.table import Table

from src.database import get_db, init_db, ensure_evidence_store, rows_to_list
from src.connectors import get_connector
from src.normalizer import normalize_items, get_evidence_stats
from src.bundler import create_bundle, export_bundle_file, build_assessment_request

console = Console()


@click.group()
def cli():
    """Evidence Collection Automator — audit evidence collection toolkit."""
    ensure_evidence_store()
    init_db()


@cli.command()
def stats():
    """Show evidence collection statistics."""
    s = get_evidence_stats()
    console.print(f"\n[bold]Evidence Collection Stats[/bold]")
    console.print(f"  Total items: {s['total_items']}")
    console.print(f"  Fresh: {s['fresh_items']}  Stale: {s['stale_items']}")
    table = Table(title="By Connector")
    table.add_column("Connector", style="cyan")
    table.add_column("Count", justify="right")
    for c in s["by_connector"]:
        table.add_row(c["name"], str(c["count"]))
    console.print(table)


@cli.command()
@click.option("--connector", "-c", required=True, help="Connector type (e.g., sim_ad, sim_mdm)")
@click.option("--market", "-m", default="Global", help="Market name")
def collect(connector: str, market: str):
    """Run a connector to collect evidence."""
    c = get_connector(connector)
    if c is None:
        console.print(f"[red]Unknown connector: {connector}[/red]")
        available = ", ".join(get_connector.__globals__["CONNECTORS"].keys())
        console.print(f"Available: {available}")
        sys.exit(1)

    console.print(f"[bold]Running {c.name} for {market}...[/bold]")
    items = c.run({}, market)

    conn = get_db()
    try:
        db_conn = conn.execute(
            "SELECT id FROM connectors WHERE connector_type = ?", (connector,)
        ).fetchone()
        if db_conn:
            from datetime import datetime
            cur = conn.execute(
                """INSERT INTO evidence_collections
                   (connector_id, user_id, market_id, status, started_at, completed_at)
                   VALUES (?, 1, NULL, 'complete', ?, ?)""",
                (db_conn["id"], datetime.utcnow().isoformat() + "Z", datetime.utcnow().isoformat() + "Z"),
            )
            collection_id = cur.lastrowid
            conn.commit()
            saved = normalize_items(items, collection_id, skip_dedup=True)
            console.print(f"[green]Collected {len(saved)} evidence items[/green]")
    finally:
        conn.close()


@cli.command()
def list_connectors():
    """List all available connectors."""
    conn = get_db()
    try:
        rows = conn.execute("SELECT * FROM connectors ORDER BY name").fetchall()
        table = Table(title="Available Connectors")
        table.add_column("ID", justify="right")
        table.add_column("Name", style="cyan")
        table.add_column("Type")
        table.add_column("Status")
        table.add_column("Last Run")
        for r in rows:
            table.add_row(str(r["id"]), r["name"], r["connector_type"], r["status"], r["last_run"] or "—")
        console.print(table)
    finally:
        conn.close()


@cli.command()
@click.option("--name", "-n", required=True, help="Bundle name")
@click.option("--items", "-i", required=True, help="Comma-separated evidence item IDs")
@click.option("--description", "-d", default="", help="Bundle description")
def bundle(name: str, items: str, description: str):
    """Create an evidence bundle."""
    item_ids = [int(i.strip()) for i in items.split(",") if i.strip()]
    result = create_bundle(user_id=1, name=name, item_ids=item_ids, description=description)
    console.print(f"[green]Bundle created: {result['id']} — {result['name']}[/green]")


@cli.command()
@click.option("--bundle-id", "-b", required=True, type=int, help="Bundle ID to export")
@click.option("--format", "-f", default="json", help="Export format (json)")
def export(bundle_id: int, format: str):
    """Export a bundle to a file."""
    path = export_bundle_file(bundle_id)
    console.print(f"[green]Exported: {path}[/green]")


@cli.command()
@click.option("--bundle-id", "-b", required=True, type=int, help="Bundle ID to assess")
def assess(bundle_id: int):
    """Build assessment payload from a bundle (for Project 1)."""
    payload = build_assessment_request(bundle_id)
    console.print(json.dumps(payload, indent=2, default=str))


if __name__ == "__main__":
    cli()

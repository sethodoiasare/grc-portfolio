"""
Evidence Bundling and Export.

Groups evidence items into named bundles and exports them as structured
JSON packages ready for import into the ITGC Evidence Analyser (Project 1).
"""

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from src.database import get_db
from src.normalizer import get_all_evidence


def create_bundle(
    user_id: int,
    name: str,
    item_ids: list[int],
    market_id: int | None = None,
    control_ids: list[str] | None = None,
    description: str = "",
) -> dict:
    conn = get_db()
    try:
        control_json = json.dumps(control_ids or [])
        item_json = json.dumps(item_ids)
        cur = conn.execute(
            """INSERT INTO evidence_bundles
               (user_id, name, description, item_ids, market_id, control_ids)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, name, description, item_json, market_id, control_json),
        )
        conn.commit()
        return get_bundle(cur.lastrowid)
    finally:
        conn.close()


def get_bundle(bundle_id: int) -> dict:
    conn = get_db()
    try:
        row = conn.execute(
            """SELECT b.*, m.name as market_name
               FROM evidence_bundles b
               LEFT JOIN markets m ON b.market_id = m.id
               WHERE b.id = ?""",
            (bundle_id,),
        ).fetchone()
        if row is None:
            return {}
        d = dict(row)
        d["item_ids"] = json.loads(d["item_ids"])
        d["control_ids"] = json.loads(d["control_ids"])
        return d
    finally:
        conn.close()


def list_bundles(user_id: int) -> list[dict]:
    conn = get_db()
    try:
        rows = conn.execute(
            """SELECT b.*, m.name as market_name
               FROM evidence_bundles b
               LEFT JOIN markets m ON b.market_id = m.id
               WHERE b.user_id = ?
               ORDER BY b.created_at DESC""",
            (user_id,),
        ).fetchall()
        results = []
        for r in rows:
            d = dict(r)
            d["item_ids"] = json.loads(d["item_ids"])
            d["control_ids"] = json.loads(d["control_ids"])
            results.append(d)
        return results
    finally:
        conn.close()


def export_bundle_json(bundle_id: int) -> dict:
    """
    Export a bundle as a structured JSON package ready for the ITGC
    Evidence Analyser. Matches Project 1's BatchAssessRequest format.
    """
    bundle = get_bundle(bundle_id)
    if not bundle:
        return {"error": "Bundle not found"}

    items = []
    for item_id in bundle["item_ids"]:
        all_evidence = get_all_evidence(limit=500)
        for ev in all_evidence:
            if ev["id"] == item_id:
                items.append(ev)
                break

    return {
        "bundle_id": bundle["id"],
        "bundle_name": bundle["name"],
        "description": bundle.get("description", ""),
        "market_id": bundle.get("market_id"),
        "market_name": bundle.get("market_name"),
        "control_ids": bundle.get("control_ids", []),
        "exported_at": datetime.utcnow().isoformat() + "Z",
        "evidence_count": len(items),
        "evidence_items": items,
        "ready_for_assessment": True,
    }


def export_bundle_file(bundle_id: int, output_dir: str | None = None) -> str:
    """Export bundle to a JSON file, returns the file path."""
    data = export_bundle_json(bundle_id)
    output_dir = output_dir or tempfile.gettempdir()
    path = Path(output_dir) / f"evidence_bundle_{bundle_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
    return str(path)


def build_assessment_request(bundle_id: int) -> dict:
    """
    Build a request payload compatible with Project 1's POST /api/v1/assess/batch.
    Maps evidence items to assessment items with control IDs and evidence text.
    """
    bundle = get_bundle(bundle_id)
    if not bundle:
        return {"error": "Bundle not found"}

    assessments = []
    for item_id in bundle["item_ids"]:
        all_evidence = get_all_evidence(limit=500)
        for ev in all_evidence:
            if ev["id"] == item_id:
                control_id = (ev.get("control_mapping") or ["UNKNOWN"])[0]
                evidence_text = json.dumps(ev.get("data", {}), default=str, indent=2)
                assessments.append({
                    "control_id": control_id,
                    "evidence_text": f"[Source: {ev.get('source_system', 'Unknown')}] "
                                    f"[Type: {ev.get('evidence_type', 'Unknown')}]\n\n"
                                    f"{evidence_text}",
                    "statement_type": "D",
                })
                break

    return {
        "audit_scope": f"Evidence Bundle: {bundle['name']}",
        "assessments": assessments,
    }

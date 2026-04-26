"""
Evidence Normalisation Engine.

Takes raw connector output and normalises it into the standard EvidenceItem
format with consistent metadata, freshness tracking, and control mapping.
Also handles deduplication.
"""

import json
from datetime import datetime, timedelta
from src.database import get_db
from src.models import EvidenceItem


def normalize_items(items: list[EvidenceItem], collection_id: int) -> list[dict]:
    """
    Normalise a list of EvidenceItems and persist them to the database.
    Returns the saved items as dicts.
    """
    conn = get_db()
    try:
        saved = []
        for item in items:
            data_json = json.dumps(item.data, default=str)
            control_json = json.dumps(item.control_mapping)
            freshness = item.freshness_date or (datetime.utcnow() + timedelta(days=90)).isoformat() + "Z"
            normalized_at = datetime.utcnow().isoformat() + "Z"

            # Check for duplicates (same source + type within 24h)
            existing = conn.execute(
                """SELECT id FROM evidence_items
                   WHERE source_system = ? AND evidence_type = ?
                   AND normalized_at > ?""",
                (item.source_system, item.evidence_type,
                 (datetime.utcnow() - timedelta(hours=24)).isoformat() + "Z"),
            ).fetchone()

            if existing:
                continue  # Skip duplicate

            cur = conn.execute(
                """INSERT INTO evidence_items
                   (collection_id, evidence_type, source_system, data_json,
                    normalized_at, freshness_date, control_mapping)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (collection_id, item.evidence_type, item.source_system,
                 data_json, normalized_at, freshness, control_json),
            )
            conn.commit()

            item.id = cur.lastrowid
            item.normalized_at = normalized_at
            saved.append(item.to_dict())

        return saved
    finally:
        conn.close()


def get_evidence_by_collection(collection_id: int) -> list[dict]:
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT * FROM evidence_items WHERE collection_id = ? ORDER BY evidence_type",
            (collection_id,),
        ).fetchall()
        results = []
        for r in rows:
            d = dict(r)
            d["data"] = json.loads(d["data_json"])
            d["control_mapping"] = json.loads(d["control_mapping"])
            results.append(d)
        return results
    finally:
        conn.close()


def get_all_evidence(
    connector_type: str | None = None,
    market_id: int | None = None,
    search: str | None = None,
    limit: int = 100,
) -> list[dict]:
    conn = get_db()
    try:
        query = """
            SELECT ei.*, ec.market_id, c.name as connector_name
            FROM evidence_items ei
            JOIN evidence_collections ec ON ei.collection_id = ec.id
            JOIN connectors c ON ec.connector_id = c.id
            WHERE 1=1
        """
        params: list = []
        if connector_type:
            query += " AND c.connector_type = ?"
            params.append(connector_type)
        if market_id:
            query += " AND ec.market_id = ?"
            params.append(market_id)
        if search:
            query += " AND (ei.evidence_type LIKE ? OR ei.source_system LIKE ? OR ei.data_json LIKE ?)"
            like = f"%{search}%"
            params.extend([like, like, like])
        query += " ORDER BY ei.normalized_at DESC LIMIT ?"
        params.append(limit)

        rows = conn.execute(query, params).fetchall()
        results = []
        for r in rows:
            d = dict(r)
            d["data"] = json.loads(d["data_json"])
            d["control_mapping"] = json.loads(d["control_mapping"])
            results.append(d)
        return results
    finally:
        conn.close()


def get_evidence_stats() -> dict:
    conn = get_db()
    try:
        total = conn.execute("SELECT COUNT(*) FROM evidence_items").fetchone()[0]
        by_connector_rows = conn.execute(
            """SELECT c.name, c.connector_type, COUNT(ei.id) as cnt
               FROM connectors c
               LEFT JOIN evidence_collections ec ON ec.connector_id = c.id
               LEFT JOIN evidence_items ei ON ei.collection_id = ec.id
               GROUP BY c.id ORDER BY cnt DESC"""
        ).fetchall()

        fresh = conn.execute(
            "SELECT COUNT(*) FROM evidence_items WHERE freshness_date > datetime('now')"
        ).fetchone()[0]
        stale = total - fresh

        return {
            "total_items": total,
            "fresh_items": fresh,
            "stale_items": stale,
            "by_connector": [{"name": r["name"], "type": r["connector_type"], "count": r["cnt"]} for r in by_connector_rows],
        }
    finally:
        conn.close()


def delete_evidence_item(item_id: int) -> bool:
    conn = get_db()
    try:
        cur = conn.execute("DELETE FROM evidence_items WHERE id = ?", (item_id,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()

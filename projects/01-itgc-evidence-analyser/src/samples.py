"""Samples CRUD operations for the ITGC Evidence Analyser."""

import json
from src.database import get_db, rows_to_list, row_to_dict


def get_samples(market_id: int, control_id: str) -> dict | None:
    """Get saved samples for a specific market + control combination."""
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT * FROM samples WHERE market_id = ? AND control_id = ?",
            (market_id, control_id),
        ).fetchone()
        if row is None:
            return None
        d = dict(row)
        d["tags"] = json.loads(d["tags"])
        return d
    finally:
        conn.close()


def save_samples(market_id: int, control_id: str, tags: list[str], user_id: int) -> dict:
    """Save or replace samples for a market + control combination."""
    conn = get_db()
    try:
        tags_json = json.dumps(tags)
        existing = conn.execute(
            "SELECT id FROM samples WHERE market_id = ? AND control_id = ?",
            (market_id, control_id),
        ).fetchone()
        if existing:
            conn.execute(
                """UPDATE samples SET tags = ?, updated_by = ?, updated_at = datetime('now')
                   WHERE market_id = ? AND control_id = ?""",
                (tags_json, user_id, market_id, control_id),
            )
        else:
            conn.execute(
                """INSERT INTO samples (market_id, control_id, tags, updated_by)
                   VALUES (?, ?, ?, ?)""",
                (market_id, control_id, tags_json, user_id),
            )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM samples WHERE market_id = ? AND control_id = ?",
            (market_id, control_id),
        ).fetchone()
        d = dict(row)
        d["tags"] = json.loads(d["tags"])
        return d
    finally:
        conn.close()


def get_all_for_market(market_id: int) -> list[dict]:
    """Get all sample definitions for a given market."""
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT * FROM samples WHERE market_id = ? ORDER BY control_id",
            (market_id,),
        ).fetchall()
        results = rows_to_list(rows)
        for r in results:
            r["tags"] = json.loads(r["tags"])
        return results
    finally:
        conn.close()

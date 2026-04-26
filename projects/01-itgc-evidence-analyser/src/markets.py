"""Markets CRUD operations for the ITGC Evidence Analyser."""

from src.database import get_db, rows_to_list, row_to_dict


def list_markets() -> list[dict]:
    conn = get_db()
    try:
        rows = conn.execute("SELECT * FROM markets ORDER BY name").fetchall()
        return rows_to_list(rows)
    finally:
        conn.close()


def search_markets(query: str) -> list[dict]:
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT * FROM markets WHERE name LIKE ? ORDER BY name",
            (f"%{query}%",),
        ).fetchall()
        return rows_to_list(rows)
    finally:
        conn.close()


def create_market(name: str, user_id: int) -> dict | None:
    conn = get_db()
    try:
        existing = conn.execute("SELECT id FROM markets WHERE name = ?", (name,)).fetchone()
        if existing:
            return None
        conn.execute(
            "INSERT INTO markets (name, created_by) VALUES (?, ?)",
            (name, user_id),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM markets WHERE name = ?", (name,)).fetchone()
        return row_to_dict(row)
    finally:
        conn.close()


def delete_market(market_id: int) -> bool:
    conn = get_db()
    try:
        cur = conn.execute("DELETE FROM markets WHERE id = ?", (market_id,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def rename_market(market_id: int, name: str) -> dict | None:
    conn = get_db()
    try:
        conn.execute("UPDATE markets SET name = ? WHERE id = ?", (name, market_id))
        conn.commit()
        row = conn.execute("SELECT * FROM markets WHERE id = ?", (market_id,)).fetchone()
        return row_to_dict(row)
    finally:
        conn.close()

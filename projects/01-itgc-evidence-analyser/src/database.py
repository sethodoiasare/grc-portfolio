"""
SQLite database layer for the ITGC Evidence Analyser.

Provides connection management, schema initialisation, and seed data.
Uses sqlite3 from stdlib — no external database server required.
"""

import sqlite3
import os
import json
from pathlib import Path

DATABASE_PATH = os.environ.get("DATABASE_PATH", str(Path(__file__).resolve().parent.parent / "data" / "itgc.db"))
EVIDENCE_STORE = os.environ.get("EVIDENCE_STORE", str(Path(__file__).resolve().parent.parent / "data" / "evidence"))

DEFAULT_MARKETS = [
    "Albania", "Czech Republic", "DRC", "Egypt", "GDC", "Germany",
    "Global Cyber Security", "Greece", "IoT", "Ireland", "Italy", "Kenya",
    "Lesotho", "Mozambique", "MPesa Africa", "Netherlands", "Spain", "Lowi",
    "Office IT", "Portugal", "Romania", "South Africa", "Tanzania", "Turkey",
    "Vodafone Automotive", "Vodafone Networks", "VBIT", "VSSI", "VSSB",
    "VSSR", "VSSE", "VFS",
]

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'auditor',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS markets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    created_by INTEGER REFERENCES users(id),
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS samples (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    market_id INTEGER NOT NULL REFERENCES markets(id) ON DELETE CASCADE,
    control_id TEXT NOT NULL,
    tags TEXT NOT NULL DEFAULT '[]',
    updated_by INTEGER REFERENCES users(id),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(market_id, control_id)
);

CREATE TABLE IF NOT EXISTS assessments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    market_id INTEGER REFERENCES markets(id),
    control_id TEXT NOT NULL,
    statement_type TEXT NOT NULL,
    samples_json TEXT DEFAULT '[]',
    verdict TEXT NOT NULL,
    result_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS evidence_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    assessment_id INTEGER NOT NULL REFERENCES assessments(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    content_type TEXT,
    file_path TEXT NOT NULL,
    extracted_text TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS chat_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    title TEXT DEFAULT 'New Chat',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    tool_calls_json TEXT,
    assessment_id INTEGER REFERENCES assessments(id),
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


def get_db() -> sqlite3.Connection:
    """Return a database connection with row factory set for dict-like access."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db(conn: sqlite3.Connection | None = None) -> None:
    """Create tables and seed default markets if the database is empty."""
    own_conn = conn is None
    if own_conn:
        conn = get_db()

    conn.executescript(SCHEMA)

    existing = conn.execute("SELECT COUNT(*) FROM markets").fetchone()[0]
    if existing == 0:
        for name in DEFAULT_MARKETS:
            conn.execute("INSERT INTO markets (name) VALUES (?)", (name,))

    if own_conn:
        conn.commit()
        conn.close()


def init_db_command() -> None:
    """CLI entry point for database initialisation."""
    print(f"Initialising database at {DATABASE_PATH} ...")
    ensure_evidence_store()
    conn = get_db()
    init_db(conn)
    conn.commit()
    count = conn.execute("SELECT COUNT(*) FROM markets").fetchone()[0]
    conn.close()
    print(f"Database ready. {count} markets seeded.")


def ensure_evidence_store() -> None:
    """Create the evidence file storage directory if it doesn't exist."""
    Path(EVIDENCE_STORE).mkdir(parents=True, exist_ok=True)


def row_to_dict(row: sqlite3.Row | None) -> dict | None:
    """Convert a sqlite3.Row to a plain dict, or None."""
    if row is None:
        return None
    return dict(row)


def rows_to_list(rows: list[sqlite3.Row]) -> list[dict]:
    """Convert a list of sqlite3.Row objects to a list of dicts."""
    return [dict(r) for r in rows]

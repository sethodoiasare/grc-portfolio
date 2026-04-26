"""
SQLite database layer for the Evidence Collection Automator.

Provides connection management, schema initialisation, and seed data.
Reuses the Project 1 database pattern with expanded schema.
"""

import sqlite3
import os
import json
from pathlib import Path

DATABASE_PATH = os.environ.get("DATABASE_PATH", str(Path(__file__).resolve().parent.parent / "data" / "evidence_collection.db"))
EVIDENCE_STORE = os.environ.get("EVIDENCE_STORE", str(Path(__file__).resolve().parent.parent / "data" / "collected"))

DEFAULT_CONNECTORS = [
    ("Active Directory", "sim_ad"),
    ("MDM / Intune", "sim_mdm"),
    ("Firewall Config", "sim_firewall"),
    ("Vulnerability Scanner", "sim_vuln"),
    ("SIEM Log Extractor", "sim_siem"),
    ("Endpoint DLP", "sim_dlp"),
    ("Manual Upload", "manual"),
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

CREATE TABLE IF NOT EXISTS connectors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    connector_type TEXT NOT NULL,
    status TEXT DEFAULT 'idle',
    last_run TEXT,
    config_json TEXT DEFAULT '{}',
    enabled INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS evidence_collections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    connector_id INTEGER REFERENCES connectors(id),
    user_id INTEGER REFERENCES users(id),
    market_id INTEGER REFERENCES markets(id),
    control_ids TEXT DEFAULT '[]',
    status TEXT DEFAULT 'running',
    started_at TEXT,
    completed_at TEXT,
    evidence_count INTEGER DEFAULT 0,
    summary_json TEXT DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS evidence_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    collection_id INTEGER REFERENCES evidence_collections(id) ON DELETE CASCADE,
    evidence_type TEXT NOT NULL,
    source_system TEXT,
    data_json TEXT NOT NULL,
    normalized_at TEXT,
    freshness_date TEXT,
    control_mapping TEXT DEFAULT '[]'
);

CREATE TABLE IF NOT EXISTS evidence_bundles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id),
    name TEXT NOT NULL,
    description TEXT,
    item_ids TEXT DEFAULT '[]',
    market_id INTEGER REFERENCES markets(id),
    control_ids TEXT DEFAULT '[]',
    created_at TEXT DEFAULT (datetime('now')),
    exported_at TEXT
);
"""

DEFAULT_MARKETS = [
    "Albania", "Czech Republic", "DRC", "Egypt", "GDC", "Germany",
    "Global Cyber Security", "Greece", "IoT", "Ireland", "Italy", "Kenya",
    "Lesotho", "Mozambique", "MPesa Africa", "Netherlands", "Spain", "Lowi",
    "Office IT", "Portugal", "Romania", "South Africa", "Tanzania", "Turkey",
    "Vodafone Automotive", "Vodafone Networks", "VBIT", "VSSI", "VSSB",
    "VSSR", "VSSE", "VFS",
]


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db(conn: sqlite3.Connection | None = None) -> None:
    own_conn = conn is None
    if own_conn:
        conn = get_db()

    conn.executescript(SCHEMA)

    existing_markets = conn.execute("SELECT COUNT(*) FROM markets").fetchone()[0]
    if existing_markets == 0:
        for name in DEFAULT_MARKETS:
            conn.execute("INSERT INTO markets (name) VALUES (?)", (name,))

    existing_connectors = conn.execute("SELECT COUNT(*) FROM connectors").fetchone()[0]
    if existing_connectors == 0:
        for name, ctype in DEFAULT_CONNECTORS:
            conn.execute(
                "INSERT INTO connectors (name, connector_type) VALUES (?, ?)",
                (name, ctype),
            )

    if own_conn:
        conn.commit()
        conn.close()


def ensure_evidence_store() -> None:
    Path(EVIDENCE_STORE).mkdir(parents=True, exist_ok=True)


def row_to_dict(row: sqlite3.Row | None) -> dict | None:
    if row is None:
        return None
    return dict(row)


def rows_to_list(rows: list[sqlite3.Row]) -> list[dict]:
    return [dict(r) for r in rows]

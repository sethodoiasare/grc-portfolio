"""
SQLite database layer for the Vuln SLA Tracker.

Schema for vulnerabilities, scanner runs, and SLA rule configuration.
"""

import sqlite3
import os
from pathlib import Path

_DEFAULT_DB_PATH = str(Path(__file__).resolve().parent.parent / "data" / "vuln_sla.db")


def _db_path() -> str:
    return os.environ.get("DATABASE_PATH", _DEFAULT_DB_PATH)


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'auditor',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS scanner_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scanner_type TEXT NOT NULL,
    filename TEXT NOT NULL,
    vulns_imported INTEGER DEFAULT 0,
    vulns_new INTEGER DEFAULT 0,
    vulns_updated INTEGER DEFAULT 0,
    imported_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS vulnerabilities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scanner_run_id INTEGER REFERENCES scanner_runs(id),
    scanner_type TEXT NOT NULL,
    asset_hostname TEXT NOT NULL,
    asset_ip TEXT NOT NULL DEFAULT '',
    title TEXT NOT NULL,
    description TEXT DEFAULT '',
    severity TEXT NOT NULL,
    cvss_score REAL DEFAULT 0.0,
    cve_id TEXT DEFAULT '',
    port INTEGER,
    protocol TEXT DEFAULT '',
    solution TEXT DEFAULT '',
    status TEXT NOT NULL DEFAULT 'open',
    first_seen TEXT NOT NULL,
    last_seen TEXT NOT NULL,
    closed_at TEXT,
    risk_accepted_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_vulns_status ON vulnerabilities(status);
CREATE INDEX IF NOT EXISTS idx_vulns_severity ON vulnerabilities(severity);
CREATE INDEX IF NOT EXISTS idx_vulns_cve ON vulnerabilities(cve_id);
CREATE INDEX IF NOT EXISTS idx_vulns_asset ON vulnerabilities(asset_hostname);
CREATE INDEX IF NOT EXISTS idx_vulns_scanner_run ON vulnerabilities(scanner_run_id);
"""


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db(conn: sqlite3.Connection | None = None) -> None:
    own_conn = conn is None
    if own_conn:
        conn = get_db()

    Path(_db_path()).parent.mkdir(parents=True, exist_ok=True)
    conn.executescript(SCHEMA)

    if own_conn:
        conn.commit()
        conn.close()


def row_to_dict(row: sqlite3.Row | None) -> dict | None:
    if row is None:
        return None
    return dict(row)


def rows_to_list(rows: list[sqlite3.Row]) -> list[dict]:
    return [dict(r) for r in rows]

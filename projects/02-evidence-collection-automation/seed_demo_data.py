#!/usr/bin/env python3
"""Seed demo data by running all 7 connectors across multiple markets."""

import json
import sys
from datetime import datetime

from src.database import get_db, init_db, ensure_evidence_store
from src.connectors import CONNECTORS
from src.normalizer import normalize_items
from src.auth import hash_password

ensure_evidence_store()
init_db()

# Clear old demo data
conn_clean = get_db()
conn_clean.execute("DELETE FROM evidence_items")
conn_clean.execute("DELETE FROM evidence_collections")
conn_clean.execute("DELETE FROM evidence_bundles")
conn_clean.execute("UPDATE connectors SET status = 'idle', last_run = NULL")
conn_clean.commit()
conn_clean.close()
print("Cleared old demo data.")

conn = get_db()
try:
    # Ensure admin user
    existing = conn.execute("SELECT id FROM users WHERE email = ?", ("admin@vodafone.com",)).fetchone()
    if not existing:
        conn.execute(
            "INSERT INTO users (email, password_hash, role) VALUES (?, ?, 'admin')",
            ("admin@vodafone.com", hash_password("GRCadmin2026!")),
        )
        conn.commit()
        user_id = conn.execute("SELECT id FROM users WHERE email = ?", ("admin@vodafone.com",)).fetchone()["id"]
    else:
        user_id = existing["id"]

    # Markets to run against
    market_ids = conn.execute("SELECT id, name FROM markets LIMIT 8").fetchall()
    if not market_ids:
        print("No markets found.")
        sys.exit(1)

    total_items = 0

    for connector_type, connector in CONNECTORS.items():
        db_conn = conn.execute(
            "SELECT id FROM connectors WHERE connector_type = ?", (connector_type,)
        ).fetchone()
        if not db_conn:
            continue

        connector_id = db_conn["id"]
        market = market_ids[(total_items // 3) % len(market_ids)]  # Rotate markets

        print(f"Running {connector.name} for {market['name']}...")

        # Mark as running
        conn.execute("UPDATE connectors SET status = 'running' WHERE id = ?", (connector_id,))
        conn.commit()

        # Create collection
        now = datetime.utcnow().isoformat() + "Z"
        cur = conn.execute(
            """INSERT INTO evidence_collections
               (connector_id, user_id, market_id, status, started_at)
               VALUES (?, ?, ?, 'running', ?)""",
            (connector_id, user_id, market["id"], now),
        )
        collection_id = cur.lastrowid
        conn.commit()

        # Run connector
        try:
            items = connector.simulate(market["name"], {})
        except Exception as e:
            print(f"  ERROR: {e}")
            conn.execute("UPDATE connectors SET status = 'error' WHERE id = ?", (connector_id,))
            conn.commit()
            continue

        # Normalize and save
        saved = normalize_items(items, collection_id, skip_dedup=True)

        # Update records
        control_ids = list(set(cid for item in items for cid in item.control_mapping))
        conn.execute(
            "UPDATE connectors SET status = 'success', last_run = ? WHERE id = ?",
            (now, connector_id),
        )
        conn.execute(
            """UPDATE evidence_collections
               SET status = 'complete', completed_at = ?, evidence_count = ?,
                   control_ids = ?, summary_json = ?
               WHERE id = ?""",
            (now, len(saved), json.dumps(control_ids),
             json.dumps({"connector": connector.name, "market": market["name"], "items_collected": len(saved)}),
             collection_id),
        )
        conn.commit()
        total_items += len(saved)
        print(f"  Collected {len(saved)} items")

    print(f"\nDone. {total_items} total evidence items across 7 connectors.")
finally:
    conn.close()

#!/usr/bin/env python3
"""Seed the first admin user. Run once after database setup."""

import sys
from src.database import get_db, init_db, ensure_evidence_store
from src.auth import hash_password

ensure_evidence_store()
init_db()

email = sys.argv[1] if len(sys.argv) > 1 else "admin@vodafone.com"
password = sys.argv[2] if len(sys.argv) > 2 else "ChangeMe123!"

conn = get_db()
try:
    hashed = hash_password(password)
    existing = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
    if existing:
        print(f"User '{email}' already exists. Updating password and role...")
        conn.execute(
            "UPDATE users SET password_hash = ?, role = 'admin' WHERE email = ?",
            (hashed, email),
        )
    else:
        conn.execute(
            "INSERT INTO users (email, password_hash, role) VALUES (?, ?, 'admin')",
            (email, hashed),
        )
    conn.commit()
    print(f"Admin user ready: {email}")
finally:
    conn.close()

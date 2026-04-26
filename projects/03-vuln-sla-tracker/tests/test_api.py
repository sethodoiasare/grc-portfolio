"""Integration tests for FastAPI endpoints."""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
import os

from src.api import app
from src.database import init_db, get_db

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "vuln_sla_api_test.db")


@pytest.fixture(autouse=True)
def _setup():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    os.environ["DATABASE_PATH"] = DB_PATH
    init_db()
    yield
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    os.environ.pop("DATABASE_PATH", None)


client = TestClient(app)


def _auth_headers():
    """Register + login and return auth headers."""
    client.post("/api/v1/auth/register", json={"email": "test@test.com", "password": "test123"})
    resp = client.post("/api/v1/auth/login", json={"email": "test@test.com", "password": "test123"})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _seed_vulns():
    """Insert test vulnerabilities directly."""
    conn = get_db()
    try:
        now = datetime.utcnow()
        conn.execute(
            """INSERT INTO scanner_runs (scanner_type, filename, vulns_imported)
               VALUES ('nessus', 'test.csv', 5)"""
        )
        for i in range(5):
            days_ago = 10 + i * 5
            conn.execute(
                """INSERT INTO vulnerabilities
                   (scanner_run_id, scanner_type, asset_hostname, title, severity, cvss_score,
                    cve_id, status, first_seen, last_seen)
                   VALUES (1, 'nessus', ?, ?, ?, ?, ?, 'open', ?, ?)""",
                (f"host{i:02d}", f"Vuln {i}", "High", 7.5, f"CVE-2024-{i:04d}",
                 (now - timedelta(days=days_ago)).isoformat() + "Z",
                 now.isoformat() + "Z"),
            )
        conn.commit()
    finally:
        conn.close()


def test_health():
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["version"] == "1.0.0"


def test_register_and_login():
    resp = client.post("/api/v1/auth/register", json={"email": "a@b.com", "password": "xyz"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "a@b.com"

    resp = client.post("/api/v1/auth/login", json={"email": "a@b.com", "password": "xyz"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_auth_me():
    headers = _auth_headers()
    resp = client.get("/api/v1/auth/me", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == "test@test.com"


def test_public_endpoints_no_auth():
    """Dashboard KPIs and scanner runs are public read endpoints."""
    resp = client.get("/api/v1/dashboard/kpis")
    assert resp.status_code == 200

    resp = client.get("/api/v1/scanner/runs")
    assert resp.status_code == 200


def test_dashboard_kpis_empty():
    resp = client.get("/api/v1/dashboard/kpis")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_open"] == 0


def test_dashboard_kpis_with_data():
    _seed_vulns()
    resp = client.get("/api/v1/dashboard/kpis")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_open"] == 5
    assert data["high_open"] == 5
    assert data["breach_rate_pct"] >= 0


def test_list_vulnerabilities():
    _seed_vulns()
    resp = client.get("/api/v1/vulnerabilities")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 5
    assert len(data["items"]) == 5
    assert "days_open" in data["items"][0]
    assert "sla_breach_days" in data["items"][0]


def test_list_vulnerabilities_filters():
    _seed_vulns()
    resp = client.get("/api/v1/vulnerabilities?severity=High")
    assert resp.status_code == 200
    assert resp.json()["total"] == 5

    resp = client.get("/api/v1/vulnerabilities?severity=Critical")
    assert resp.status_code == 200
    assert resp.json()["total"] == 0

    resp = client.get("/api/v1/vulnerabilities?search=host01")
    assert resp.status_code == 200
    assert resp.json()["total"] == 1


def test_get_single_vulnerability():
    _seed_vulns()
    resp = client.get("/api/v1/vulnerabilities/1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == 1
    assert "sla_breach_days" in data


def test_update_vulnerability():
    _seed_vulns()
    headers = _auth_headers()
    resp = client.patch("/api/v1/vulnerabilities/1", json={"status": "closed"}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "closed"
    assert resp.json()["closed_at"] is not None

    # Invalid status
    resp = client.patch("/api/v1/vulnerabilities/1", json={"status": "invalid"}, headers=headers)
    assert resp.status_code == 422


def test_top_overdue():
    _seed_vulns()
    resp = client.get("/api/v1/dashboard/top-overdue?limit=3")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) <= 3


def test_severity_distribution():
    _seed_vulns()
    resp = client.get("/api/v1/dashboard/severity-distribution")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1  # Only High severity
    assert data[0]["severity"] == "High"


def test_breach_timeline():
    _seed_vulns()
    resp = client.get("/api/v1/dashboard/breach-timeline?days=7")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 8  # 7 days + today


def test_scanner_runs():
    _seed_vulns()
    resp = client.get("/api/v1/scanner/runs")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["scanner_type"] == "nessus"


def test_export_csv():
    _seed_vulns()
    resp = client.get("/api/v1/export/vulnerabilities")
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]
    assert "dc01" not in resp.text.lower()  # Shouldn't have dc01 — our test hosts are different


def test_import_scanner_csv():
    headers = _auth_headers()
    csv_content = """Host,Host IP,Name,Description,Risk,CVSS,Port,Protocol,Solution,CVE
dc01.example.com,10.1.1.10,Test Vuln,Test desc,Critical,9.8,445,tcp,Patch it,CVE-2024-99999
"""
    resp = client.post(
        "/api/v1/scanner/import?scanner_type=nessus",
        files={"file": ("nessus_scan.csv", csv_content.encode(), "text/csv")},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["vulns_imported"] == 1
    assert data["vulns_new"] == 1
    assert data["run_id"] is not None


def test_scanner_import_invalid_type():
    headers = _auth_headers()
    resp = client.post(
        "/api/v1/scanner/import?scanner_type=invalid",
        files={"file": ("test.csv", b"data", "text/csv")},
        headers=headers,
    )
    assert resp.status_code == 422

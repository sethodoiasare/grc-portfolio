"""Integration tests for the FastAPI application."""

import pytest
from fastapi.testclient import TestClient

from src.api import app


@pytest.fixture
def client():
    return TestClient(app)


def test_health_check(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert "audit" in data["service"]


def test_api_dashboard_returns_valid_data(client):
    resp = client.get("/api/dashboard")
    assert resp.status_code == 200
    data = resp.json()
    assert "projects" in data
    assert "controls" in data
    assert "deadlines" in data
    assert "overall_rag" in data
    assert "summary" in data
    assert data["overall_rag"] in ("GREEN", "AMBER", "RED")


def test_api_projects_returns_12(client):
    resp = client.get("/api/projects")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 12
    project_ids = [p["project_id"] for p in data]
    assert "P1" in project_ids
    assert "P12" in project_ids


def test_api_project_detail(client):
    resp = client.get("/api/projects/P1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["project_id"] == "P1"
    assert data["name"] == "ITGC Evidence Analyser"
    assert "test_count" in data


def test_api_project_not_found(client):
    resp = client.get("/api/projects/P99")
    assert resp.status_code == 404


def test_api_controls(client):
    resp = client.get("/api/controls")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 30
    for c in data:
        assert "control_id" in c
        assert "category" in c
        assert "covered_by" in c
        assert "status" in c
        assert c["status"] in ("COVERED", "PARTIAL", "GAP")


def test_api_controls_filtered(client):
    resp = client.get("/api/controls?category=Access Control")
    assert resp.status_code == 200
    data = resp.json()
    for c in data:
        assert c["category"] == "Access Control"


def test_api_control_gaps(client):
    resp = client.get("/api/controls/gaps")
    assert resp.status_code == 200
    data = resp.json()
    for c in data:
        assert c["status"] in ("PARTIAL", "GAP")


def test_api_deadlines_sorted(client):
    resp = client.get("/api/deadlines")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 5
    days = [d["days_remaining"] for d in data]
    assert days == sorted(days)


def test_api_stats(client):
    resp = client.get("/api/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_projects"] == 12
    assert data["total_tests"] > 700
    assert data["controls_total"] >= 30
    assert "projects_green" in data
    assert "projects_amber" in data
    assert "projects_red" in data


def test_serve_dashboard_html(client):
    resp = client.get("/")
    assert resp.status_code == 200
    html = resp.text
    assert "<!DOCTYPE html>" in html
    assert "Audit Readiness Dashboard" in html
    assert "GRC Portfolio" in html
    assert 'class="project-card' in html

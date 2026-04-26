import pytest
import json
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from src.api import app
from src.models import (
    AssessmentResult, Verdict, RiskRating, StatementType, DraftFinding
)
from datetime import datetime


def make_mock_result(control_id="IAM_001", verdict=Verdict.PASS):
    return AssessmentResult(
        control_id=control_id,
        control_name="User Registration and De-registration",
        statement_type=StatementType.DESIGN,
        verdict=verdict,
        confidence=0.90,
        satisfied_requirements=["D1: complete"],
        gaps=[],
        risk_rating=RiskRating.INFORMATIONAL,
        draft_finding=None,
        recommended_evidence=[],
        remediation_notes="",
        assessed_at=datetime(2026, 1, 15, 10, 0, 0),
        tokens_used=1000,
        model_used="claude-sonnet-4-6",
    )


MOCK_USER = {"id": 1, "email": "test@test.com", "role": "admin", "created_at": "2026-01-01T00:00:00"}


@pytest.fixture(autouse=True)
def bypass_auth():
    """Override the get_current_user dependency so tests don't need real JWTs."""
    app.dependency_overrides = {}
    from src.auth import get_current_user, require_admin
    async def _mock_user():
        return MOCK_USER
    async def _mock_admin():
        return MOCK_USER
    app.dependency_overrides[get_current_user] = _mock_user
    app.dependency_overrides[require_admin] = _mock_admin
    yield
    app.dependency_overrides = {}


@pytest.fixture
def client():
    return TestClient(app)


def test_health_returns_ok(client):
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["controls_loaded"] == 58


def test_list_controls_returns_all(client):
    resp = client.get("/api/v1/controls")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 58


def test_list_controls_filter_by_domain(client):
    resp = client.get("/api/v1/controls?domain=IAM")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) > 0
    assert all(c["domain"] == "IAM" for c in data)


def test_get_control_iam001_returns_correct(client):
    resp = client.get("/api/v1/controls/IAM_001")
    assert resp.status_code == 200
    data = resp.json()
    assert data["control_id"] == "IAM_001"
    assert "d_statements" in data


def test_get_control_unknown_returns_404(client):
    resp = client.get("/api/v1/controls/DOES_NOT_EXIST")
    assert resp.status_code == 404


def test_search_controls(client):
    resp = client.get("/api/v1/controls/search?q=privileged")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) > 0


def test_assess_endpoint_with_mock(client):
    mock_result = make_mock_result()
    with patch("src.api._assessor.assess", return_value=mock_result):
        resp = client.post(
            "/api/v1/assess",
            json={"control_id": "IAM_001", "evidence_text": "Some evidence", "statement_type": "D"},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["verdict"] == "PASS"
    assert data["control_id"] == "IAM_001"


def test_assess_endpoint_unknown_control_returns_404(client):
    with patch("src.api._assessor.assess", side_effect=ValueError("Control 'FAKE' not found")):
        resp = client.post(
            "/api/v1/assess",
            json={"control_id": "FAKE", "evidence_text": "Evidence", "statement_type": "D"},
        )
    assert resp.status_code == 404


def test_assess_endpoint_invalid_statement_type(client):
    resp = client.post(
        "/api/v1/assess",
        json={"control_id": "IAM_001", "evidence_text": "Evidence", "statement_type": "X"},
    )
    assert resp.status_code == 422


def test_batch_assess_returns_report(client):
    mock_results = [make_mock_result("IAM_001"), make_mock_result("VUL_001")]
    with patch("src.api._assessor.assess_batch", return_value=mock_results):
        resp = client.post(
            "/api/v1/assess/batch",
            json={
                "audit_scope": "Test scope",
                "assessments": [
                    {"control_id": "IAM_001", "evidence_text": "E1"},
                    {"control_id": "VUL_001", "evidence_text": "E2"},
                ],
            },
        )
    assert resp.status_code == 200
    data = resp.json()
    assert "summary" in data
    assert data["summary"]["total_controls_assessed"] == 2


def test_markets_list(client):
    resp = client.get("/api/v1/markets")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 32


def test_markets_search(client):
    resp = client.get("/api/v1/markets/search?q=czech")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["name"] == "Czech Republic"


def test_unified_search(client):
    resp = client.get("/api/v1/search?q=mobile")
    assert resp.status_code == 200
    data = resp.json()
    assert "controls" in data
    assert "markets" in data


def test_auth_me(client):
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "test@test.com"


def test_auth_register(client):
    import uuid
    email = f"auditor_{uuid.uuid4().hex[:8]}@test.com"
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "pass123", "role": "auditor"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == email


def test_auth_login(client):
    import uuid
    email = f"login_{uuid.uuid4().hex[:8]}@test.com"
    # Register first
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "pass123", "role": "auditor"},
    )
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "pass123"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["user"]["email"] == email

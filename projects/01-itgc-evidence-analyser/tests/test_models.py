import pytest
from datetime import datetime
from src.models import (
    Verdict, RiskRating, StatementType,
    DraftFinding, AssessmentResult,
)


def make_finding():
    return DraftFinding(
        title="Missing access review",
        observation="No quarterly access review completed",
        criteria="D4 requires quarterly review",
        risk_impact="Unauthorised accounts may persist",
        recommendation="Implement quarterly access review process",
        management_action="Review to be completed by Q2 2026",
    )


def make_result(verdict=Verdict.FAIL, finding=True):
    return AssessmentResult(
        control_id="IAM_001",
        control_name="User Registration and De-registration",
        statement_type=StatementType.DESIGN,
        verdict=verdict,
        confidence=0.85,
        satisfied_requirements=["D1: procedure exists", "D2: approvals in place"],
        gaps=["D4: no quarterly review", "D5: procedure outdated"],
        risk_rating=RiskRating.HIGH,
        draft_finding=make_finding() if finding else None,
        recommended_evidence=["Quarterly review records", "Procedure sign-off"],
        remediation_notes="Implement a formal quarterly access review.",
        tokens_used=1500,
        model_used="claude-sonnet-4-6",
    )


def test_verdict_enum_values():
    assert Verdict.PASS == "PASS"
    assert Verdict.FAIL == "FAIL"
    assert Verdict.PARTIAL == "PARTIAL"
    assert Verdict.INSUFFICIENT_EVIDENCE == "INSUFFICIENT_EVIDENCE"


def test_risk_rating_enum_values():
    assert RiskRating.CRITICAL == "CRITICAL"
    assert RiskRating.HIGH == "HIGH"


def test_statement_type_enum_values():
    assert StatementType.DESIGN == "D"
    assert StatementType.EVIDENCE == "E"


def test_draft_finding_to_dict():
    f = make_finding()
    d = f.to_dict()
    assert d["title"] == "Missing access review"
    assert "observation" in d
    assert "recommendation" in d
    assert len(d) == 6


def test_assessment_result_is_pass_false_for_fail():
    r = make_result(Verdict.FAIL)
    assert r.is_pass is False


def test_assessment_result_is_pass_true_for_pass():
    r = make_result(Verdict.PASS, finding=False)
    assert r.is_pass is True


def test_assessment_result_has_finding_true():
    r = make_result(Verdict.FAIL, finding=True)
    assert r.has_finding is True


def test_assessment_result_has_finding_false():
    r = make_result(Verdict.PASS, finding=False)
    assert r.has_finding is False


def test_assessment_result_gap_count():
    r = make_result(Verdict.FAIL)
    assert r.gap_count == 2


def test_assessment_result_to_dict_keys():
    r = make_result(Verdict.PARTIAL)
    d = r.to_dict()
    expected = {
        "control_id", "control_name", "statement_type", "verdict", "confidence",
        "satisfied_requirements", "gaps", "risk_rating", "draft_finding",
        "recommended_evidence", "remediation_notes", "assessed_at",
        "tokens_used", "model_used",
    }
    assert expected.issubset(d.keys())


def test_assessment_result_to_dict_verdict_is_string():
    r = make_result(Verdict.FAIL)
    d = r.to_dict()
    assert d["verdict"] == "FAIL"
    assert isinstance(d["verdict"], str)


def test_assessment_result_to_dict_draft_finding_nested():
    r = make_result(Verdict.FAIL)
    d = r.to_dict()
    assert d["draft_finding"] is not None
    assert "title" in d["draft_finding"]


def test_assessment_result_to_dict_no_finding_is_none():
    r = make_result(Verdict.PASS, finding=False)
    d = r.to_dict()
    assert d["draft_finding"] is None


def test_assessment_result_to_json_is_valid_json():
    import json
    r = make_result(Verdict.PARTIAL)
    j = r.to_json()
    parsed = json.loads(j)
    assert parsed["control_id"] == "IAM_001"


def test_assessed_at_defaults_to_utcnow():
    r = make_result(Verdict.PASS, finding=False)
    assert isinstance(r.assessed_at, datetime)

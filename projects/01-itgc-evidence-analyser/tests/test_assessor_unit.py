import pytest
from unittest.mock import patch, MagicMock
from src.assessor import EvidenceAssessor
from src.models import Verdict, RiskRating, AssessmentResult, DraftFinding


MOCK_PASS_RESPONSE = {
    "verdict": "PASS",
    "confidence": 0.92,
    "satisfied_requirements": ["D1: procedure documented", "D2: approval workflow active"],
    "gaps": [],
    "risk_rating": "INFORMATIONAL",
    "draft_finding": None,
    "recommended_evidence": [],
    "remediation_notes": "Control is operating effectively.",
}

MOCK_FAIL_RESPONSE = {
    "verdict": "FAIL",
    "confidence": 0.88,
    "satisfied_requirements": ["D1: procedure exists"],
    "gaps": ["D2: no approvals on access requests", "D4: leaver process not automated"],
    "risk_rating": "HIGH",
    "draft_finding": {
        "title": "Access provisioning lacks formal approval",
        "observation": "Access tickets sampled showed no evidence of approver sign-off",
        "criteria": "D2 requires approver sign-off prior to account creation",
        "risk_impact": "Unauthorised access may be granted",
        "recommendation": "Implement mandatory approval workflow in ITSM",
        "management_action": "ServiceNow workflow update by 30 June 2026",
    },
    "recommended_evidence": ["Sample access tickets with approvals", "ITSM workflow config"],
    "remediation_notes": "Mandate approver field in all access request tickets.",
}

MOCK_PARTIAL_RESPONSE = {
    "verdict": "PARTIAL",
    "confidence": 0.75,
    "satisfied_requirements": ["D1: procedure exists", "D3: unique user IDs enforced"],
    "gaps": ["D4: leaver deactivation SLA exceeded in 3 of 10 samples"],
    "risk_rating": "MEDIUM",
    "draft_finding": {
        "title": "Leaver deactivation SLA not consistently met",
        "observation": "3 of 10 sampled leaver events exceeded the 1 business day deactivation SLA",
        "criteria": "D4 requires account deactivation within one business day of leaver event",
        "risk_impact": "Former employees retain system access beyond authorised period",
        "recommendation": "Automate HR-to-AD deactivation trigger",
        "management_action": "Automation project scoped for Q3 2026",
    },
    "recommended_evidence": ["HR leaver report with timestamps", "AD deactivation logs"],
    "remediation_notes": "Automate the Workday-to-Active Directory deactivation trigger.",
}


@pytest.fixture
def assessor():
    return EvidenceAssessor()


def test_assess_pass_returns_pass_verdict(assessor):
    with patch.object(assessor.client, "assess_evidence", return_value=(MOCK_PASS_RESPONSE, 1200)):
        result = assessor.assess("IAM_001", "Some evidence text", "D")
    assert result.verdict == Verdict.PASS
    assert result.is_pass is True
    assert result.draft_finding is None


def test_assess_fail_returns_fail_verdict_with_finding(assessor):
    with patch.object(assessor.client, "assess_evidence", return_value=(MOCK_FAIL_RESPONSE, 1500)):
        result = assessor.assess("IAM_001", "Some evidence text", "D")
    assert result.verdict == Verdict.FAIL
    assert result.draft_finding is not None
    assert result.draft_finding.title == "Access provisioning lacks formal approval"
    assert result.risk_rating == RiskRating.HIGH
    assert result.gap_count == 2


def test_assess_partial_returns_draft_finding(assessor):
    with patch.object(assessor.client, "assess_evidence", return_value=(MOCK_PARTIAL_RESPONSE, 1300)):
        result = assessor.assess("IAM_001", "Some partial evidence", "D")
    assert result.verdict == Verdict.PARTIAL
    assert result.has_finding is True
    assert result.confidence == 0.75


def test_assess_tokens_recorded(assessor):
    with patch.object(assessor.client, "assess_evidence", return_value=(MOCK_PASS_RESPONSE, 999)):
        result = assessor.assess("IAM_001", "Evidence", "D")
    assert result.tokens_used == 999


def test_assess_unknown_control_raises(assessor):
    with pytest.raises(ValueError, match="not found"):
        assessor.assess("NONEXISTENT_001", "some evidence", "D")


def test_assess_batch_returns_multiple_results(assessor):
    items = [
        {"control_id": "IAM_001", "evidence_text": "Evidence A", "statement_type": "D"},
        {"control_id": "VULN_MGMT_001", "evidence_text": "Evidence B", "statement_type": "D"},
    ]
    with patch.object(assessor.client, "assess_evidence", return_value=(MOCK_PASS_RESPONSE, 1000)):
        results = assessor.assess_batch(items)
    assert len(results) == 2
    assert all(isinstance(r, AssessmentResult) for r in results)


def test_assess_batch_preserves_order(assessor):
    items = [
        {"control_id": "IAM_001", "evidence_text": "E1"},
        {"control_id": "VULN_MGMT_001", "evidence_text": "E2"},
        {"control_id": "BCM_001", "evidence_text": "E3"},
    ]
    with patch.object(assessor.client, "assess_evidence", return_value=(MOCK_PASS_RESPONSE, 500)):
        results = assessor.assess_batch(items)
    assert results[0].control_id == "IAM_001"
    assert results[1].control_id == "VULN_MGMT_001"
    assert results[2].control_id == "BCM_001"


def test_assess_from_file_reads_txt(tmp_path, assessor):
    f = tmp_path / "evidence.txt"
    f.write_text("This is a test evidence file.")
    with patch.object(assessor.client, "assess_evidence", return_value=(MOCK_PASS_RESPONSE, 800)):
        result = assessor.assess_from_file("IAM_001", str(f), "D")
    assert result.verdict == Verdict.PASS

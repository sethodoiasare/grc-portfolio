"""Tests for domain models."""

from src.models import (
    Question, CategoryScore, VendorAssessment,
    Answer, Weight, RiskRating,
    ANSWER_SCORE, WEIGHT_MULTIPLIER,
)


def test_question_creation():
    q = Question(id="Q-001", category="AccessControl", text="MFA enforced?", weight=Weight.HIGH, answer=Answer.YES)
    assert q.id == "Q-001"
    assert q.category == "AccessControl"
    assert q.weight == Weight.HIGH
    assert q.answer == Answer.YES
    assert q.is_scored() is True


def test_question_na_is_not_scored():
    q = Question(id="Q-002", category="Compliance", text="PCI DSS?", weight=Weight.LOW, answer=Answer.NA)
    assert q.is_scored() is False
    assert q.weighted_score() == 0.0
    assert q.max_possible() == 0.0


def test_question_weighted_score_yes_high():
    q = Question(id="Q-003", category="Encryption", text="Encryption at rest?", weight=Weight.HIGH, answer=Answer.YES)
    assert q.weighted_score() == 3.0  # 1.0 * 3
    assert q.max_possible() == 3.0


def test_question_weighted_score_partial_medium():
    q = Question(id="Q-004", category="BCP", text="DR site?", weight=Weight.MEDIUM, answer=Answer.PARTIAL)
    assert q.weighted_score() == 1.0  # 0.5 * 2
    assert q.max_possible() == 2.0


def test_question_weighted_score_no_low():
    q = Question(id="Q-005", category="Compliance", text="Bug bounty?", weight=Weight.LOW, answer=Answer.NO)
    assert q.weighted_score() == 0.0  # 0.0 * 1
    assert q.max_possible() == 1.0


def test_answer_score_values():
    assert ANSWER_SCORE[Answer.YES] == 1.0
    assert ANSWER_SCORE[Answer.PARTIAL] == 0.5
    assert ANSWER_SCORE[Answer.NO] == 0.0


def test_weight_multiplier_values():
    assert WEIGHT_MULTIPLIER[Weight.HIGH] == 3
    assert WEIGHT_MULTIPLIER[Weight.MEDIUM] == 2
    assert WEIGHT_MULTIPLIER[Weight.LOW] == 1


def test_category_score_creation():
    cs = CategoryScore(category="AccessControl", total_weighted=9.0, max_possible=9.0, pct=100.0, risk_level=RiskRating.LOW)
    assert cs.category == "AccessControl"
    assert cs.pct == 100.0
    assert cs.risk_level == RiskRating.LOW


def test_vendor_assessment_to_dict():
    q = Question(id="Q-001", category="AccessControl", text="MFA?", weight=Weight.HIGH, answer=Answer.YES)
    cs = CategoryScore(category="AccessControl", total_weighted=3.0, max_possible=3.0, pct=100.0, risk_level=RiskRating.LOW)
    a = VendorAssessment(
        vendor_name="TestCorp",
        assessment_date="2026-04-29",
        questions=[q],
        category_scores=[cs],
        overall_score=95.0,
        risk_rating=RiskRating.LOW,
        top_risks=[],
        remediation_checklist=[],
    )
    d = a.to_dict()
    assert d["vendor_name"] == "TestCorp"
    assert d["overall_score"] == 95.0
    assert d["risk_rating"] == "LOW"
    assert len(d["questions"]) == 1


def test_question_to_dict():
    q = Question(id="Q-042", category="Encryption", text="TLS 1.2+?", weight=Weight.HIGH, answer=Answer.YES, notes="ok")
    d = q.to_dict()
    assert d["id"] == "Q-042"
    assert d["weight"] == "HIGH"
    assert d["answer"] == "YES"
    assert d["notes"] == "ok"

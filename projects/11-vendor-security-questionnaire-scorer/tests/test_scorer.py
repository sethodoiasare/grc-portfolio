"""Tests for the scoring engine."""

import pytest
from src.models import Question, Answer, Weight, RiskRating, CATEGORIES
from src.scorer import (
    score_questions, calculate_overall, determine_risk_rating,
    identify_top_risks, generate_remediation, assess_vendor,
)


def _q(cat: str, text: str, weight: str, answer: str, idx: int = 1) -> Question:
    return Question(id=f"Q-{idx:03d}", category=cat, text=text,
                    weight=Weight(weight), answer=Answer(answer))


def test_all_yes_answers_score_100_low_risk():
    questions = [
        _q("AccessControl", "Q1", "HIGH", "YES", 1),
        _q("DataProtection", "Q2", "HIGH", "YES", 2),
        _q("Encryption", "Q3", "HIGH", "YES", 3),
        _q("IncidentResponse", "Q4", "HIGH", "YES", 4),
        _q("BCP", "Q5", "HIGH", "YES", 5),
        _q("SupplierMgmt", "Q6", "HIGH", "YES", 6),
        _q("Compliance", "Q7", "HIGH", "YES", 7),
    ]
    assessment = assess_vendor("TestVendor", questions)
    assert assessment.overall_score == 100.0
    assert assessment.risk_rating == RiskRating.LOW


def test_all_no_answers_score_0_critical_risk():
    questions = [
        _q("AccessControl", "Q1", "HIGH", "NO", 1),
        _q("DataProtection", "Q2", "HIGH", "NO", 2),
        _q("Encryption", "Q3", "HIGH", "NO", 3),
        _q("IncidentResponse", "Q4", "HIGH", "NO", 4),
        _q("BCP", "Q5", "HIGH", "NO", 5),
        _q("SupplierMgmt", "Q6", "HIGH", "NO", 6),
        _q("Compliance", "Q7", "HIGH", "NO", 7),
    ]
    assessment = assess_vendor("TestVendor", questions)
    assert assessment.overall_score == 0.0
    assert assessment.risk_rating == RiskRating.CRITICAL


def test_mixed_answers_with_weighting():
    questions = [
        _q("AccessControl", "Q1", "HIGH", "YES", 1),     # 3/3
        _q("AccessControl", "Q2", "MEDIUM", "PARTIAL", 2),  # 1/2
        _q("AccessControl", "Q3", "LOW", "NO", 3),         # 0/1
    ]
    # AccessControl: (3+1+0) / (3+2+1) = 4/6 = 66.7%
    category_scores = score_questions(questions)
    ac = next(cs for cs in category_scores if cs.category == "AccessControl")
    assert ac.total_weighted == 4.0
    assert ac.max_possible == 6.0
    assert ac.pct == pytest.approx(66.7, abs=0.1)


def test_na_questions_excluded_from_scoring():
    questions = [
        _q("AccessControl", "Q1", "HIGH", "YES", 1),     # 3/3
        _q("AccessControl", "Q2", "HIGH", "NA", 2),       # excluded
        _q("AccessControl", "Q3", "HIGH", "NO", 3),        # 0/3
    ]
    # AccessControl: (3+0) / (3+3) = 3/6 = 50%
    category_scores = score_questions(questions)
    ac = next(cs for cs in category_scores if cs.category == "AccessControl")
    assert ac.total_weighted == 3.0
    assert ac.max_possible == 6.0
    assert ac.pct == 50.0


def test_category_scoring_correct():
    questions = [
        _q("AccessControl", "AC1", "HIGH", "YES", 1),        # 3/3
        _q("AccessControl", "AC2", "MEDIUM", "YES", 2),      # 2/2
        _q("AccessControl", "AC3", "LOW", "YES", 3),          # 1/1
        _q("Encryption", "ENC1", "HIGH", "NO", 4),            # 0/3
        _q("Encryption", "ENC2", "MEDIUM", "PARTIAL", 5),     # 1/2
    ]
    category_scores = score_questions(questions)

    ac = next(cs for cs in category_scores if cs.category == "AccessControl")
    assert ac.pct == 100.0

    enc = next(cs for cs in category_scores if cs.category == "Encryption")
    assert enc.total_weighted == 1.0   # 0 + 1
    assert enc.max_possible == 5.0     # 3 + 2
    assert enc.pct == 20.0


def test_empty_category_returns_100():
    """Categories with no questions should default to 100% (no gaps found)."""
    questions: list[Question] = []
    category_scores = score_questions(questions)
    for cs in category_scores:
        assert cs.max_possible == 0.0
        assert cs.pct == 100.0


def test_risk_thresholds():
    # >=85 = LOW
    assert determine_risk_rating(100.0) == RiskRating.LOW
    assert determine_risk_rating(85.0) == RiskRating.LOW  # boundary
    # >=70 = MEDIUM
    assert determine_risk_rating(84.9) == RiskRating.MEDIUM
    assert determine_risk_rating(70.0) == RiskRating.MEDIUM  # boundary
    # >=50 = HIGH
    assert determine_risk_rating(69.9) == RiskRating.HIGH
    assert determine_risk_rating(50.0) == RiskRating.HIGH  # boundary
    # <50 = CRITICAL
    assert determine_risk_rating(49.9) == RiskRating.CRITICAL
    assert determine_risk_rating(0.0) == RiskRating.CRITICAL


def test_top_risks_identified_correctly():
    questions = [
        _q("Encryption", "Enc at rest missing", "HIGH", "NO", 1),
        _q("DataProtection", "Classification missing", "HIGH", "NO", 2),
        _q("AccessControl", "MFA OK", "HIGH", "YES", 3),
        _q("Compliance", "Minor gap", "MEDIUM", "NO", 4),    # not HIGH, not top risk
        _q("BCP", "DR gap", "HIGH", "PARTIAL", 5),            # not NO, not top risk
        _q("SupplierMgmt", "N/A question", "HIGH", "NA", 6),   # NA excluded
    ]
    risks = identify_top_risks(questions)
    assert len(risks) == 2
    assert any("Enc at rest missing" in r for r in risks)
    assert any("Classification missing" in r for r in risks)
    assert not any("Minor gap" in r for r in risks)


def test_remediation_generated_for_no_and_partial_only():
    questions = [
        _q("Encryption", "Enc at rest", "HIGH", "NO", 1),
        _q("BCP", "DR site", "MEDIUM", "PARTIAL", 2),
        _q("AccessControl", "MFA", "HIGH", "YES", 3),
        _q("Compliance", "PCI DSS", "LOW", "NA", 4),
    ]
    items = generate_remediation(questions)
    # Q1 NO + Q2 PARTIAL = 2 remediation items. Q3 YES and Q4 NA get none.
    assert len(items) == 2
    assert any("Enc at rest" in item for item in items)
    assert any("DR site" in item for item in items)
    assert not any("MFA" in item for item in items)
    assert not any("PCI DSS" in item for item in items)


def test_overall_score_is_category_average():
    """Overall score should be the average of category scores (equal weight per category)."""
    questions = [
        _q("AccessControl", "AC1", "HIGH", "YES", 1),        # 100%
        _q("DataProtection", "DP1", "HIGH", "NO", 2),         # 0%
        _q("Encryption", "ENC1", "HIGH", "YES", 3),           # 100%
        _q("IncidentResponse", "IR1", "HIGH", "YES", 4),      # 100%
        _q("BCP", "BCP1", "HIGH", "NO", 5),                   # 0%
        _q("SupplierMgmt", "SM1", "HIGH", "YES", 6),          # 100%
        _q("Compliance", "C1", "HIGH", "YES", 7),             # 100%
    ]
    assessment = assess_vendor("TestVendor", questions)
    # 5 categories at 100%, 2 at 0% → (100*5 + 0*2) / 7 = 71.4%
    assert assessment.overall_score == pytest.approx(71.4, abs=0.1)
    assert assessment.risk_rating == RiskRating.MEDIUM

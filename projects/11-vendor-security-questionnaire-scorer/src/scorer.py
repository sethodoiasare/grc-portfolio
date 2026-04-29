"""Scoring engine for vendor security questionnaires."""

from datetime import date
from collections import defaultdict

from .models import (
    Question, CategoryScore, VendorAssessment, RiskRating,
    Answer, Weight, CATEGORIES, RISK_THRESHOLDS,
)


def score_questions(questions: list[Question]) -> list[CategoryScore]:
    """Compute per-category scores from a list of questions.

    For each category, sums the weighted scores of all scored (non-NA)
    questions and divides by the maximum possible weighted score.
    """
    cat_weighted: dict[str, float] = defaultdict(float)
    cat_max: dict[str, float] = defaultdict(float)

    for q in questions:
        if q.is_scored():
            cat_weighted[q.category] += q.weighted_score()
            cat_max[q.category] += q.max_possible()

    category_scores: list[CategoryScore] = []
    for cat in CATEGORIES:
        total = cat_weighted.get(cat, 0.0)
        max_possible = cat_max.get(cat, 0.0)
        if max_possible > 0:
            pct = (total / max_possible) * 100
        else:
            pct = 100.0  # No scored questions in this category — treat as compliant

        risk_level = _threshold_for(pct)
        category_scores.append(CategoryScore(
            category=cat,
            total_weighted=round(total, 2),
            max_possible=round(max_possible, 2),
            pct=round(pct, 1),
            risk_level=risk_level,
        ))

    return category_scores


def calculate_overall(category_scores: list[CategoryScore]) -> float:
    """Weighted average across categories, normalized to 0-100.

    Each category contributes equally. Categories with no scored questions
    (max_possible == 0) are excluded from the average.
    """
    scored_cats = [cs for cs in category_scores if cs.max_possible > 0]
    if not scored_cats:
        return 100.0

    total_pct = sum(cs.pct for cs in scored_cats)
    return round(total_pct / len(scored_cats), 1)


def determine_risk_rating(overall_score: float) -> RiskRating:
    """Apply thresholds to determine risk rating."""
    for threshold, rating in RISK_THRESHOLDS:
        if overall_score >= threshold:
            return rating
    return RiskRating.CRITICAL


def identify_top_risks(questions: list[Question]) -> list[str]:
    """Identify NO-answered HIGH-weight questions as top risks."""
    risks: list[str] = []
    for q in questions:
        if q.answer == Answer.NO and q.weight == Weight.HIGH and q.is_scored():
            risks.append(f"[{q.category}] {q.text}")
    return risks


def generate_remediation(questions: list[Question]) -> list[str]:
    """Generate a remediation action item for each NO or PARTIAL answer."""
    items: list[str] = []
    for q in questions:
        if not q.is_scored():
            continue
        if q.answer == Answer.NO:
            items.append(
                f"[{q.category}] {q.text} — Vendor response was NO. "
                f"Require remediation plan with committed timeline before contract signing."
            )
        elif q.answer == Answer.PARTIAL:
            items.append(
                f"[{q.category}] {q.text} — Vendor response was PARTIAL. "
                f"Request evidence of partial implementation and gap-closure roadmap."
            )
    return items


def assess_vendor(vendor_name: str, questions: list[Question]) -> VendorAssessment:
    """Full scoring pipeline: questions -> category scores -> overall -> risks -> remediation."""
    category_scores = score_questions(questions)
    overall = calculate_overall(category_scores)
    rating = determine_risk_rating(overall)
    top_risks = identify_top_risks(questions)
    remediation = generate_remediation(questions)

    return VendorAssessment(
        vendor_name=vendor_name,
        assessment_date=date.today().isoformat(),
        questions=questions,
        category_scores=category_scores,
        overall_score=overall,
        risk_rating=rating,
        top_risks=top_risks,
        remediation_checklist=remediation,
    )


def _threshold_for(pct: float) -> RiskRating:
    for threshold, rating in RISK_THRESHOLDS:
        if pct >= threshold:
            return rating
    return RiskRating.CRITICAL

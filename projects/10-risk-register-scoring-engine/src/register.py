"""Risk register operations: CRUD, workflows, filtering, and matrix generation."""

from copy import deepcopy
from dataclasses import asdict
from datetime import date, timedelta
from typing import Optional

from .models import (
    Risk, RiskRegister, RiskCategory, RiskStatus, RiskLevel,
    SSVCMetric, SSVCDecision,
)
from .cvss_calc import parse_cvss_vector, calculate_cvss_score, get_severity
from .ssvc_calc import calculate_ssvc


def _compute_risk_level(impact_score: int, likelihood_score: int) -> RiskLevel:
    """Compute risk level from 0-100 impact and likelihood scores.

    Bins each score into 1-5, then applies the standard 5x5 matrix:
      1-4: LOW, 5-9: MEDIUM, 10-19: HIGH, 20-25: CRITICAL.
    """
    def _bin(score: int) -> int:
        if score <= 20:
            return 1
        elif score <= 40:
            return 2
        elif score <= 60:
            return 3
        elif score <= 80:
            return 4
        else:
            return 5

    impact_bin = _bin(impact_score)
    likelihood_bin = _bin(likelihood_score)
    product = impact_bin * likelihood_bin

    if product <= 4:
        return RiskLevel.LOW
    elif product <= 9:
        return RiskLevel.MEDIUM
    elif product <= 19:
        return RiskLevel.HIGH
    else:
        return RiskLevel.CRITICAL


def _next_risk_id(register: RiskRegister) -> str:
    """Generate the next sequential risk ID."""
    existing = [int(r.risk_id[4:]) for r in register.risks if r.risk_id.startswith("RSK-")]
    if not existing:
        return "RSK-001"
    return f"RSK-{max(existing) + 1:03d}"


def create_risk(
    title: str,
    description: str,
    category: RiskCategory,
    cvss_vector: str,
    ssvc_metric: SSVCMetric,
    owner: str = "",
    impact_score: int = 50,
    likelihood_score: int = 50,
    identified_date: Optional[date] = None,
    treatment_plan: str = "",
    control_mapping: Optional[list[str]] = None,
) -> Risk:
    """Create a fully-scored Risk.

    Args:
        title: Short risk title.
        description: Detailed description.
        category: RiskCategory enum value.
        cvss_vector: CVSS v3.1 vector string.
        ssvc_metric: SSVCMetric with all fields set.
        owner: Risk owner identifier.
        impact_score: Business impact score 0-100.
        likelihood_score: Likelihood score 0-100.
        identified_date: Date risk was identified (defaults to today).
        treatment_plan: Planned treatment approach.
        control_mapping: List of control IDs mapped to this risk.

    Returns:
        A Risk instance with computed scores and level.
    """
    metrics = parse_cvss_vector(cvss_vector)
    cvss_score = calculate_cvss_score(metrics)
    ssvc_decision = calculate_ssvc(
        ssvc_metric.exploitation,
        ssvc_metric.automatable,
        ssvc_metric.technical_impact,
        ssvc_metric.mission_impact,
    )
    risk_level = _compute_risk_level(impact_score, likelihood_score)

    return Risk(
        risk_id="",  # placeholder, assigned on register add
        title=title,
        description=description,
        category=category,
        owner=owner,
        identified_date=identified_date or date.today(),
        status=RiskStatus.IDENTIFIED,
        cvss_score=cvss_score,
        cvss_vector=cvss_vector,
        ssvc_decision=ssvc_decision,
        impact_score=impact_score,
        likelihood_score=likelihood_score,
        risk_level=risk_level,
        treatment_plan=treatment_plan,
        control_mapping=control_mapping or [],
    )


def add_to_register(register: RiskRegister, risk: Risk) -> Risk:
    """Add a risk to the register with an auto-assigned ID."""
    risk.risk_id = _next_risk_id(register)
    register.add(risk)
    return risk


def update_risk(register: RiskRegister, risk_id: str, updates: dict) -> Optional[Risk]:
    """Partially update a risk in the register.

    Recomputes risk_level if impact_score or likelihood_score change.
    Does NOT recompute CVSS or SSVC from partial updates.

    Args:
        register: The RiskRegister.
        risk_id: ID of the risk to update.
        updates: Dict of field name -> new value.

    Returns:
        Updated Risk, or None if not found.
    """
    risk = register.get(risk_id)
    if risk is None:
        return None

    for key, value in updates.items():
        if hasattr(risk, key):
            setattr(risk, key, value)

    # Recompute risk level if impact or likelihood changed
    if "impact_score" in updates or "likelihood_score" in updates:
        risk.risk_level = _compute_risk_level(risk.impact_score, risk.likelihood_score)

    register.updated = date.today().isoformat()
    return risk


def accept_risk(
    risk: Risk,
    rationale: str,
    accepted_by: str,
    review_days: int = 90,
) -> Risk:
    """Accept a risk with rationale and review timeline.

    Args:
        risk: The risk to accept.
        rationale: Business justification for acceptance.
        accepted_by: Identifier of the person accepting the risk.
        review_days: Days until next review.

    Returns:
        The updated Risk.
    """
    risk.status = RiskStatus.ACCEPTED
    risk.acceptance_rationale = rationale
    risk.owner = accepted_by
    risk.review_date = date.today() + timedelta(days=review_days)
    return risk


def mitigate_risk(risk: Risk, treatment_plan: str) -> Risk:
    """Mark a risk as mitigated with a treatment plan.

    Args:
        risk: The risk to mitigate.
        treatment_plan: Description of the mitigation measures.

    Returns:
        The updated Risk.
    """
    risk.status = RiskStatus.MITIGATED
    risk.treatment_plan = treatment_plan
    return risk


def close_risk(risk: Risk) -> Risk:
    """Close a risk (e.g., after verification of mitigation).

    Args:
        risk: The risk to close.

    Returns:
        The updated Risk.
    """
    risk.status = RiskStatus.CLOSED
    return risk


# Risk Matrix ------------------------------------------------------------

def get_risk_matrix(register: RiskRegister) -> dict:
    """Build a 5x5 likelihood x impact matrix with risk counts per cell.

    Returns a dict with keys:
      - 'cells': 2D list (5x5) where cells[likelihood-1][impact-1] = count
      - 'risks_by_cell': map of "L{I}-I{J}" -> list of risk dicts
    """
    cells = [[0 for _ in range(5)] for _ in range(5)]
    risks_by_cell: dict[str, list] = {}

    def _bin(score: int) -> int:
        if score <= 20:
            return 1
        elif score <= 40:
            return 2
        elif score <= 60:
            return 3
        elif score <= 80:
            return 4
        else:
            return 5

    for risk in register.risks:
        li = _bin(risk.likelihood_score) - 1
        im = _bin(risk.impact_score) - 1
        cells[li][im] += 1
        key = f"L{li + 1}-I{im + 1}"
        if key not in risks_by_cell:
            risks_by_cell[key] = []
        risks_by_cell[key].append({
            "risk_id": risk.risk_id,
            "title": risk.title,
            "risk_level": risk.risk_level.value,
            "cvss_score": risk.cvss_score,
        })

    return {"cells": cells, "risks_by_cell": risks_by_cell}


# Filtering --------------------------------------------------------------

def filter_by_status(register: RiskRegister, status: RiskStatus) -> list[Risk]:
    """Filter risks by status."""
    return [r for r in register.risks if r.status == status]


def filter_by_category(register: RiskRegister, category: RiskCategory) -> list[Risk]:
    """Filter risks by category."""
    return [r for r in register.risks if r.category == category]


def filter_by_level(register: RiskRegister, level: RiskLevel) -> list[Risk]:
    """Filter risks by risk level."""
    return [r for r in register.risks if r.risk_level == level]


def get_overdue_reviews(register: RiskRegister) -> list[Risk]:
    """Return risks whose review_date has passed."""
    today = date.today()
    return [
        r for r in register.risks
        if r.review_date is not None and r.review_date < today
    ]

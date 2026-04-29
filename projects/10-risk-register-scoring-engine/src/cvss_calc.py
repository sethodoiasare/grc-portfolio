"""CVSS v3.1 base score calculator.

Implements the full CVSS v3.1 specification formulas for the Base Score,
including Scope-dependent Privileges Required values and the Scope Changed
impact formula.
"""

import math
import re
from .models import (
    AttackVector, AttackComplexity, PrivilegesRequired, UserInteraction,
    Scope, CIAImpact, CVSSMetric,
)

# CVSS v3.1 metric weights (Table 1-2 in the spec)
_AV_WEIGHTS = {
    AttackVector.NETWORK: 0.85,
    AttackVector.ADJACENT: 0.62,
    AttackVector.LOCAL: 0.55,
    AttackVector.PHYSICAL: 0.20,
}

_AC_WEIGHTS = {
    AttackComplexity.LOW: 0.77,
    AttackComplexity.HIGH: 0.44,
}

# PR weights depend on Scope
_PR_WEIGHTS_UNCHANGED = {
    PrivilegesRequired.NONE: 0.85,
    PrivilegesRequired.LOW: 0.62,
    PrivilegesRequired.HIGH: 0.27,
}

_PR_WEIGHTS_CHANGED = {
    PrivilegesRequired.NONE: 0.85,
    PrivilegesRequired.LOW: 0.68,
    PrivilegesRequired.HIGH: 0.50,
}

_UI_WEIGHTS = {
    UserInteraction.NONE: 0.85,
    UserInteraction.REQUIRED: 0.62,
}

_CIA_WEIGHTS = {
    CIAImpact.NONE: 0.00,
    CIAImpact.LOW: 0.22,
    CIAImpact.HIGH: 0.56,
}


def parse_cvss_vector(vector_string: str) -> CVSSMetric:
    """Parse a CVSS v3.1 vector string into a CVSSMetric.

    Args:
        vector_string: e.g. "AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"

    Returns:
        CVSSMetric with parsed components.

    Raises:
        ValueError: If the vector string is malformed or contains invalid values.
    """
    # Strip CVSS:3.1/ prefix if present
    cleaned = vector_string
    if cleaned.startswith("CVSS:3.1/"):
        cleaned = cleaned[len("CVSS:3.1/"):]

    parts = cleaned.split("/")
    if len(parts) < 8:
        raise ValueError(
            f"CVSS vector requires at least 8 components, got {len(parts)}: {vector_string}"
        )

    parsed: dict[str, str] = {}
    for part in parts:
        part = part.strip()
        if not part:
            continue
        if ":" not in part:
            raise ValueError(f"Invalid CVSS component (missing colon): '{part}'")
        key, value = part.split(":", 1)
        parsed[key.upper()] = value.upper()

    required = {"AV", "AC", "PR", "UI", "S", "C", "I", "A"}
    missing = required - set(parsed.keys())
    if missing:
        raise ValueError(f"CVSS vector missing required metrics: {missing}")

    av_map = {v.value: v for v in AttackVector}
    ac_map = {v.value: v for v in AttackComplexity}
    pr_map = {v.value: v for v in PrivilegesRequired}
    ui_map = {v.value: v for v in UserInteraction}
    s_map = {v.value: v for v in Scope}
    cia_map = {v.value: v for v in CIAImpact}

    def _get(mapping, key, label):
        val = parsed.get(key)
        if val not in mapping:
            raise ValueError(f"Invalid {label} value '{val}' in CVSS vector")
        return mapping[val]

    return CVSSMetric(
        av=_get(av_map, "AV", "AttackVector"),
        ac=_get(ac_map, "AC", "AttackComplexity"),
        pr=_get(pr_map, "PR", "PrivilegesRequired"),
        ui=_get(ui_map, "UI", "UserInteraction"),
        s=_get(s_map, "S", "Scope"),
        c=_get(cia_map, "C", "Confidentiality"),
        i=_get(cia_map, "I", "Integrity"),
        a=_get(cia_map, "A", "Availability"),
    )


def calculate_cvss_score(metrics: CVSSMetric) -> float:
    """Calculate the CVSS v3.1 Base Score from metrics.

    Implements the full CVSS v3.1 specification formulas:
    - Exploitability Sub Score (ESS) = 8.22 * AV * AC * PR * UI
    - Impact Sub Score (ISS) = 1 - [(1-C) * (1-I) * (1-A)]
    - Impact = 6.42 * ISS (Unchanged) or 7.52*(ISS-0.029) - 3.25*(ISS*0.9731-0.02)^13 (Changed)
    - Base = Roundup(min(Impact + Exploitability, 10)) for Unchanged
    - Base = Roundup(min(1.08 * (Impact + Exploitability), 10)) for Changed
    - If Impact <= 0, Base = 0.0

    Args:
        metrics: CVSSMetric with all components set.

    Returns:
        Float score between 0.0 and 10.0, rounded up to 1 decimal place.
    """
    av = _AV_WEIGHTS[metrics.av]
    ac = _AC_WEIGHTS[metrics.ac]

    if metrics.s == Scope.CHANGED:
        pr = _PR_WEIGHTS_CHANGED[metrics.pr]
    else:
        pr = _PR_WEIGHTS_UNCHANGED[metrics.pr]

    ui = _UI_WEIGHTS[metrics.ui]
    c = _CIA_WEIGHTS[metrics.c]
    i_val = _CIA_WEIGHTS[metrics.i]
    a = _CIA_WEIGHTS[metrics.a]

    # Exploitability Sub Score
    ess = 8.22 * av * ac * pr * ui

    # Impact Sub Score
    iss = 1.0 - ((1.0 - c) * (1.0 - i_val) * (1.0 - a))

    # Impact score
    if metrics.s == Scope.UNCHANGED:
        impact = 6.42 * iss
    else:
        # Scope Changed formula from CVSS v3.1 spec
        impact = 7.52 * (iss - 0.029) - 3.25 * ((iss * 0.9731 - 0.02) ** 13)

    if impact <= 0.0:
        return 0.0

    if metrics.s == Scope.UNCHANGED:
        base = min(impact + ess, 10.0)
    else:
        base = min(1.08 * (impact + ess), 10.0)

    # Round up to 1 decimal place
    return _roundup1(base)


def _roundup1(value: float) -> float:
    """Round up to 1 decimal place as per CVSS specification."""
    return math.ceil(value * 10.0) / 10.0


def get_severity(score: float) -> str:
    """Map a CVSS score to a severity label.

    Args:
        score: CVSS base score (0.0-10.0).

    Returns:
        One of: NONE, LOW, MEDIUM, HIGH, CRITICAL.
    """
    if score == 0.0:
        return "NONE"
    elif score <= 3.9:
        return "LOW"
    elif score <= 6.9:
        return "MEDIUM"
    elif score <= 8.9:
        return "HIGH"
    else:
        return "CRITICAL"

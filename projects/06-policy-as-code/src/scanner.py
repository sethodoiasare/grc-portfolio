"""Orchestration: evaluate all policies against input data."""

import uuid
from datetime import datetime, timezone
from typing import Optional

from .models import (
    POLICIES, PolicyReport, PolicyResult, Verdict,
)
from .evaluator import evaluate


def scan(input_data: list[dict], policy_ids: Optional[list[str]] = None) -> PolicyReport:
    """Run all policies (or a subset) against the provided input data.

    Each dict in `input_data` must contain a `_policy_id` key to match
    against the policy it should be evaluated with.
    """
    policies = [p for p in POLICIES if policy_ids is None or p["id"] in policy_ids]
    results: list[PolicyResult] = []

    for policy in policies:
        matching_resources = [r for r in input_data if r.get("_policy_id") == policy["id"]]
        for resource in matching_resources:
            results.append(evaluate(policy, resource))

    compliant = sum(1 for r in results if r.verdict == Verdict.COMPLIANT)
    non_compliant = sum(1 for r in results if r.verdict == Verdict.NON_COMPLIANT)
    errors = sum(1 for r in results if r.verdict == Verdict.ERROR)

    return PolicyReport(
        report_id=str(uuid.uuid4()),
        generated_at=datetime.now(timezone.utc).isoformat(),
        engine="python-native",
        total_policies=len(results),
        compliant=compliant,
        non_compliant=non_compliant,
        errors=errors,
        results=results,
    )

"""SSVC v2 decision calculator.

Implements the CISA Stakeholder-Specific Vulnerability Categorization (SSVC)
version 2 decision tree for vulnerability prioritization.
"""

from .models import (
    Exploitation, Automatable, TechnicalImpact, MissionImpact,
    SSVCDecision, SSVCMetric,
)


# SSVC v2 decision tree as a nested lookup.
# Structure: exploitation -> automatable -> technical_impact -> mission_impact -> decision
_SSVC_TREE: dict = {
    Exploitation.ACTIVE: {
        Automatable.YES: {
            TechnicalImpact.TOTAL: {
                MissionImpact.HIGH: SSVCDecision.ACT,
                MissionImpact.MEDIUM: SSVCDecision.ACT,
                MissionImpact.LOW: SSVCDecision.ACT,
            },
            TechnicalImpact.PARTIAL: {
                MissionImpact.HIGH: SSVCDecision.ACT,
                MissionImpact.MEDIUM: SSVCDecision.ATTEND,
                MissionImpact.LOW: SSVCDecision.ATTEND,
            },
        },
        Automatable.NO: {
            TechnicalImpact.TOTAL: {
                MissionImpact.HIGH: SSVCDecision.ACT,
                MissionImpact.MEDIUM: SSVCDecision.ATTEND,
                MissionImpact.LOW: SSVCDecision.ATTEND,
            },
            TechnicalImpact.PARTIAL: {
                MissionImpact.HIGH: SSVCDecision.ATTEND,
                MissionImpact.MEDIUM: SSVCDecision.ATTEND,
                MissionImpact.LOW: SSVCDecision.TRACK_STAR,
            },
        },
    },
    Exploitation.POC: {
        Automatable.YES: {
            TechnicalImpact.TOTAL: {
                MissionImpact.HIGH: SSVCDecision.ACT,
                MissionImpact.MEDIUM: SSVCDecision.ATTEND,
                MissionImpact.LOW: SSVCDecision.ATTEND,
            },
            TechnicalImpact.PARTIAL: {
                MissionImpact.HIGH: SSVCDecision.ATTEND,
                MissionImpact.MEDIUM: SSVCDecision.ATTEND,
                MissionImpact.LOW: SSVCDecision.TRACK_STAR,
            },
        },
        Automatable.NO: {
            TechnicalImpact.TOTAL: {
                MissionImpact.HIGH: SSVCDecision.ATTEND,
                MissionImpact.MEDIUM: SSVCDecision.ATTEND,
                MissionImpact.LOW: SSVCDecision.TRACK_STAR,
            },
            TechnicalImpact.PARTIAL: {
                MissionImpact.HIGH: SSVCDecision.ATTEND,
                MissionImpact.MEDIUM: SSVCDecision.TRACK_STAR,
                MissionImpact.LOW: SSVCDecision.TRACK,
            },
        },
    },
    Exploitation.NONE: {
        Automatable.YES: {
            TechnicalImpact.TOTAL: {
                MissionImpact.HIGH: SSVCDecision.ATTEND,
                MissionImpact.MEDIUM: SSVCDecision.ATTEND,
                MissionImpact.LOW: SSVCDecision.TRACK_STAR,
            },
            TechnicalImpact.PARTIAL: {
                MissionImpact.HIGH: SSVCDecision.ATTEND,
                MissionImpact.MEDIUM: SSVCDecision.TRACK_STAR,
                MissionImpact.LOW: SSVCDecision.TRACK,
            },
        },
        Automatable.NO: {
            TechnicalImpact.TOTAL: {
                MissionImpact.HIGH: SSVCDecision.ATTEND,
                MissionImpact.MEDIUM: SSVCDecision.TRACK_STAR,
                MissionImpact.LOW: SSVCDecision.TRACK_STAR,
            },
            TechnicalImpact.PARTIAL: {
                MissionImpact.HIGH: SSVCDecision.TRACK_STAR,
                MissionImpact.MEDIUM: SSVCDecision.TRACK,
                MissionImpact.LOW: SSVCDecision.TRACK,
            },
        },
    },
}


def calculate_ssvc(
    exploitation: Exploitation,
    automatable: Automatable,
    technical_impact: TechnicalImpact,
    mission_impact: MissionImpact,
) -> SSVCDecision:
    """Apply the SSVC v2 decision tree to determine the prioritization decision.

    Args:
        exploitation: State of exploitation (NONE, POC, ACTIVE).
        automatable: Whether the vulnerability is automatable (YES, NO).
        technical_impact: Technical impact level (PARTIAL, TOTAL).
        mission_impact: Mission/business impact level (LOW, MEDIUM, HIGH).

    Returns:
        SSVCDecision: TRACK, TRACK_STAR, ATTEND, or ACT.
    """
    return _SSVC_TREE[exploitation][automatable][technical_impact][mission_impact]


def calculate_ssvc_from_metric(metrics: SSVCMetric) -> SSVCDecision:
    """Calculate SSVC decision from an SSVCMetric object.

    Args:
        metrics: SSVCMetric with all components set.

    Returns:
        SSVCDecision.
    """
    return calculate_ssvc(
        metrics.exploitation,
        metrics.automatable,
        metrics.technical_impact,
        metrics.mission_impact,
    )


def ssvc_to_action(decision: SSVCDecision) -> str:
    """Map an SSVC decision to a recommended action description.

    Args:
        decision: The SSVC decision.

    Returns:
        Human-readable action recommendation.
    """
    actions = {
        SSVCDecision.ACT: (
            "ACT: Immediate remediation required. Deploy fix as soon as possible. "
            "Escalate to incident response if exploitation is confirmed."
        ),
        SSVCDecision.ATTEND: (
            "ATTEND: Schedule remediation within the current planning cycle. "
            "Add to active work queue and monitor for exploitation status changes."
        ),
        SSVCDecision.TRACK_STAR: (
            "TRACK*: Monitor closely. Review during the next remediation cycle. "
            "Re-evaluate if exploitation status or technical impact changes."
        ),
        SSVCDecision.TRACK: (
            "TRACK: Monitor during routine review cycles. "
            "No immediate action required but continue to track for status changes."
        ),
    }
    return actions[decision]

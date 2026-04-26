"""
Domain Models

Defines the core data structures used throughout the GRC Evidence Analyser,
from raw assessment results through to draft audit findings.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from datetime import datetime
import json


class Verdict(str, Enum):
    """Overall compliance verdict for a control assessment."""

    PASS = "PASS"
    PARTIAL = "PARTIAL"
    FAIL = "FAIL"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class RiskRating(str, Enum):
    """Risk severity rating attached to a gap or finding."""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFORMATIONAL = "INFORMATIONAL"


class StatementType(str, Enum):
    """Whether the assessment targeted design or evidence statements."""

    DESIGN = "D"
    EVIDENCE = "E"


@dataclass
class DraftFinding:
    """
    A structured audit finding produced when a control assessment returns
    a verdict of FAIL or PARTIAL. Follows the standard Vodafone/ITGC finding
    format: title, observation, criteria, risk impact, recommendation, and
    proposed management action.
    """

    title: str
    observation: str
    criteria: str
    risk_impact: str
    recommendation: str
    management_action: str

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "observation": self.observation,
            "criteria": self.criteria,
            "risk_impact": self.risk_impact,
            "recommendation": self.recommendation,
            "management_action": self.management_action,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)


@dataclass
class AssessmentResult:
    """
    The complete output of a single control assessment run by the analyser.

    Attributes
    ----------
    control_id : str
        The Vodafone control identifier, e.g. "IAM_001".
    control_name : str
        Human-readable control name.
    statement_type : StatementType
        Whether design (D) or evidence (E) statements were assessed.
    verdict : Verdict
        The overall compliance verdict determined by the model.
    confidence : float
        Model-reported confidence score in the range [0.0, 1.0].
    satisfied_requirements : list[str]
        Statement IDs (e.g. ["D1", "D3"]) that the evidence satisfies.
    gaps : list[str]
        Plain-language descriptions of each identified compliance gap.
    risk_rating : RiskRating
        Aggregate risk severity of the identified gaps.
    draft_finding : Optional[DraftFinding]
        Populated for FAIL and PARTIAL verdicts; None for PASS.
    recommended_evidence : list[str]
        Additional evidence items the auditor should request to close gaps
        or to upgrade an INSUFFICIENT_EVIDENCE verdict.
    remediation_notes : str
        Narrative guidance on how the control owner should remediate findings.
    follow_up_questions : list[str]
        Recommended follow-up questions for audit interviews or evidence requests.
    compliance_status : str
        Overall compliance status: FULL, PARTIAL, NON-COMPLIANT, or NOT_ASSESSABLE.
    audit_opinion : str
        Executive summary of the assessment in formal audit language.
    assessment_methodology : str
        Description of evidence evaluation approach and documents reviewed.
    evidence_inventory : list[dict]
        Catalogue of every evidence item with type, date, strength rating.
    requirement_assessment : list[dict]
        Per-statement assessment with status, evidence reference, and detail.
    justification : str
        Comprehensive justification of the verdict, audit-defensible.
    limitations : list[str]
        Known limitations of the evidence affecting the assessment.
    assessed_at : datetime
        UTC timestamp of when the assessment was completed.
    tokens_used : int
        Total tokens consumed (prompt + completion) for cost tracking.
    model_used : str
        The Claude model identifier used for this assessment run.
    """

    control_id: str
    control_name: str
    statement_type: StatementType
    verdict: Verdict
    confidence: float
    satisfied_requirements: list[str]
    gaps: list[str]
    risk_rating: RiskRating
    draft_finding: Optional[DraftFinding]
    recommended_evidence: list[str]
    remediation_notes: str
    follow_up_questions: list[str] = field(default_factory=list)
    compliance_status: str = ""
    audit_opinion: str = ""
    assessment_methodology: str = ""
    evidence_inventory: list = field(default_factory=list)
    requirement_assessment: list = field(default_factory=list)
    justification: str = ""
    limitations: list = field(default_factory=list)
    assessed_at: datetime = field(default_factory=datetime.utcnow)
    tokens_used: int = 0
    model_used: str = ""

    def to_dict(self) -> dict:
        return {
            "control_id": self.control_id,
            "control_name": self.control_name,
            "statement_type": self.statement_type.value,
            "verdict": self.verdict.value,
            "confidence": self.confidence,
            "satisfied_requirements": self.satisfied_requirements,
            "gaps": self.gaps,
            "risk_rating": self.risk_rating.value,
            "draft_finding": self.draft_finding.to_dict() if self.draft_finding else None,
            "recommended_evidence": self.recommended_evidence,
            "remediation_notes": self.remediation_notes,
            "follow_up_questions": self.follow_up_questions,
            "compliance_status": self.compliance_status,
            "audit_opinion": self.audit_opinion,
            "assessment_methodology": self.assessment_methodology,
            "evidence_inventory": self.evidence_inventory,
            "requirement_assessment": self.requirement_assessment,
            "justification": self.justification,
            "limitations": self.limitations,
            "assessed_at": self.assessed_at.isoformat(),
            "tokens_used": self.tokens_used,
            "model_used": self.model_used,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    @property
    def is_pass(self) -> bool:
        return self.verdict == Verdict.PASS

    @property
    def has_finding(self) -> bool:
        return self.draft_finding is not None

    @property
    def gap_count(self) -> int:
        return len(self.gaps)

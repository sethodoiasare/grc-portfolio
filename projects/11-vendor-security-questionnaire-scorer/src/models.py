"""Domain models for Vendor Security Questionnaire Scorer."""

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional


class Answer(str, Enum):
    YES = "YES"
    NO = "NO"
    PARTIAL = "PARTIAL"
    NA = "NA"


class Weight(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class RiskRating(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


CATEGORIES = [
    "AccessControl",
    "DataProtection",
    "Encryption",
    "IncidentResponse",
    "BCP",
    "SupplierMgmt",
    "Compliance",
]

WEIGHT_MULTIPLIER = {Weight.HIGH: 3, Weight.MEDIUM: 2, Weight.LOW: 1}

ANSWER_SCORE = {Answer.YES: 1.0, Answer.PARTIAL: 0.5, Answer.NO: 0.0}

RISK_THRESHOLDS = [
    (85, RiskRating.LOW),
    (70, RiskRating.MEDIUM),
    (50, RiskRating.HIGH),
]


@dataclass
class Question:
    id: str
    category: str
    text: str
    weight: Weight
    answer: Answer
    notes: str = ""

    def is_scored(self) -> bool:
        return self.answer != Answer.NA

    def weighted_score(self) -> float:
        if not self.is_scored():
            return 0.0
        return ANSWER_SCORE[self.answer] * WEIGHT_MULTIPLIER[self.weight]

    def max_possible(self) -> float:
        if not self.is_scored():
            return 0.0
        return 1.0 * WEIGHT_MULTIPLIER[self.weight]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "category": self.category,
            "text": self.text,
            "weight": self.weight.value,
            "answer": self.answer.value,
            "notes": self.notes,
        }


@dataclass
class CategoryScore:
    category: str
    total_weighted: float
    max_possible: float
    pct: float
    risk_level: RiskRating

    def to_dict(self) -> dict:
        return {
            "category": self.category,
            "total_weighted": self.total_weighted,
            "max_possible": self.max_possible,
            "pct": round(self.pct, 1),
            "risk_level": self.risk_level.value,
        }


@dataclass
class VendorAssessment:
    vendor_name: str
    assessment_date: str
    questions: list[Question] = field(default_factory=list)
    category_scores: list[CategoryScore] = field(default_factory=list)
    overall_score: float = 0.0
    risk_rating: RiskRating = RiskRating.LOW
    top_risks: list[str] = field(default_factory=list)
    remediation_checklist: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "vendor_name": self.vendor_name,
            "assessment_date": self.assessment_date,
            "questions": [q.to_dict() for q in self.questions],
            "category_scores": [cs.to_dict() for cs in self.category_scores],
            "overall_score": round(self.overall_score, 1),
            "risk_rating": self.risk_rating.value,
            "top_risks": self.top_risks,
            "remediation_checklist": self.remediation_checklist,
        }

"""Data models for the Risk Register + Scoring Engine."""

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Optional


class RiskCategory(str, Enum):
    INFRASTRUCTURE = "INFRASTRUCTURE"
    APPLICATION = "APPLICATION"
    DATA = "DATA"
    VENDOR = "VENDOR"
    HUMAN = "HUMAN"
    COMPLIANCE = "COMPLIANCE"


class RiskStatus(str, Enum):
    IDENTIFIED = "IDENTIFIED"
    ANALYZING = "ANALYZING"
    ACCEPTED = "ACCEPTED"
    MITIGATED = "MITIGATED"
    CLOSED = "CLOSED"


class RiskLevel(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class AttackVector(str, Enum):
    NETWORK = "N"
    ADJACENT = "A"
    LOCAL = "L"
    PHYSICAL = "P"


class AttackComplexity(str, Enum):
    LOW = "L"
    HIGH = "H"


class PrivilegesRequired(str, Enum):
    NONE = "N"
    LOW = "L"
    HIGH = "H"


class UserInteraction(str, Enum):
    NONE = "N"
    REQUIRED = "R"


class Scope(str, Enum):
    UNCHANGED = "U"
    CHANGED = "C"


class CIAImpact(str, Enum):
    NONE = "N"
    LOW = "L"
    HIGH = "H"


class Exploitation(str, Enum):
    NONE = "NONE"
    POC = "POC"
    ACTIVE = "ACTIVE"


class Automatable(str, Enum):
    YES = "YES"
    NO = "NO"


class TechnicalImpact(str, Enum):
    PARTIAL = "PARTIAL"
    TOTAL = "TOTAL"


class MissionImpact(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class SSVCDecision(str, Enum):
    TRACK = "TRACK"
    TRACK_STAR = "TRACK_STAR"
    ATTEND = "ATTEND"
    ACT = "ACT"


@dataclass
class CVSSMetric:
    """CVSS v3.1 metrics."""
    av: AttackVector
    ac: AttackComplexity
    pr: PrivilegesRequired
    ui: UserInteraction
    s: Scope
    c: CIAImpact
    i: CIAImpact
    a: CIAImpact


@dataclass
class SSVCMetric:
    """SSVC v2 metrics."""
    exploitation: Exploitation
    automatable: Automatable
    technical_impact: TechnicalImpact
    mission_impact: MissionImpact


@dataclass
class Risk:
    """A single risk entry in the register."""
    risk_id: str
    title: str
    description: str
    category: RiskCategory
    owner: str
    identified_date: date
    status: RiskStatus
    cvss_score: float
    cvss_vector: str
    ssvc_decision: SSVCDecision
    impact_score: int
    likelihood_score: int
    risk_level: RiskLevel
    acceptance_rationale: Optional[str] = None
    treatment_plan: str = ""
    review_date: Optional[date] = None
    control_mapping: list[str] = field(default_factory=list)


@dataclass
class RiskRegister:
    """A collection of risks with metadata."""
    risks: list[Risk] = field(default_factory=list)
    created: str = field(default_factory=lambda: datetime.now().isoformat())
    updated: str = field(default_factory=lambda: datetime.now().isoformat())
    owner: str = ""

    def add(self, risk: Risk) -> None:
        self.risks.append(risk)
        self.updated = datetime.now().isoformat()

    def get(self, risk_id: str) -> Optional[Risk]:
        for r in self.risks:
            if r.risk_id == risk_id:
                return r
        return None

    def remove(self, risk_id: str) -> bool:
        for i, r in enumerate(self.risks):
            if r.risk_id == risk_id:
                self.risks.pop(i)
                self.updated = datetime.now().isoformat()
                return True
        return False

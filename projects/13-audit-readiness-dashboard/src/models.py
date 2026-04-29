"""Data models for the Audit Readiness Dashboard."""

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional


class ProjectType(str, Enum):
    CLI = "CLI"
    WEB = "WEB"


class ProjectStatus(str, Enum):
    COMPLETE = "COMPLETE"
    IN_PROGRESS = "IN_PROGRESS"
    NEEDS_REVIEW = "NEEDS_REVIEW"


class RAG(str, Enum):
    GREEN = "GREEN"
    AMBER = "AMBER"
    RED = "RED"


class CoverageStatus(str, Enum):
    COVERED = "COVERED"
    PARTIAL = "PARTIAL"
    GAP = "GAP"


@dataclass
class ProjectInfo:
    project_id: str
    name: str
    type: ProjectType
    status: ProjectStatus
    test_count: int
    last_audit_date: str
    controls_covered: list[str]
    evidence_freshness_days: int
    rag: RAG
    description: str = ""
    port: Optional[int] = None


@dataclass
class ControlCoverage:
    control_id: str
    control_name: str
    category: str
    covered_by: list[str]
    status: CoverageStatus
    last_verified: str


@dataclass
class Deadline:
    id: str
    description: str
    date: str
    days_remaining: int
    related_control: str
    priority: str  # HIGH, MEDIUM, LOW


@dataclass
class SummaryStats:
    total_projects: int
    total_tests: int
    controls_covered: int
    controls_total: int
    controls_gap: int
    controls_partial: int
    upcoming_deadlines: int
    projects_green: int
    projects_amber: int
    projects_red: int


@dataclass
class DashboardData:
    projects: list[ProjectInfo] = field(default_factory=list)
    controls: list[ControlCoverage] = field(default_factory=list)
    deadlines: list[Deadline] = field(default_factory=list)
    overall_rag: RAG = RAG.AMBER
    summary: Optional[SummaryStats] = None
    generated_at: str = ""


def to_dict(obj):
    """Convert dataclass instance to dict, handling enums and nested objects."""
    if isinstance(obj, Enum):
        return obj.value
    if hasattr(obj, "__dataclass_fields__"):
        return {k: to_dict(v) for k, v in asdict(obj).items()}
    if isinstance(obj, list):
        return [to_dict(item) for item in obj]
    return obj

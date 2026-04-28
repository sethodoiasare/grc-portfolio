"""Domain models for DevSecOps audit evidence."""

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional
import uuid
from datetime import datetime, timezone


class Verdict(str, Enum):
    SATISFIED = "SATISFIED"
    PARTIAL = "PARTIAL"
    NOT_MET = "NOT_MET"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ArtifactType(str, Enum):
    SAST = "SAST"
    SCA = "SCA"
    SECRETS = "SECRETS"
    DAST = "DAST"
    PIPELINE_LOG = "PIPELINE_LOG"


@dataclass
class SASTFinding:
    check_id: str
    path: str
    severity: Severity
    message: str
    line: Optional[int] = None
    rule_name: Optional[str] = None


@dataclass
class SCAFinding:
    package_name: str
    version: str
    vulnerability_id: str
    severity: Severity
    fixed_version: Optional[str] = None
    advisory: Optional[str] = None


@dataclass
class SecretFinding:
    description: str
    file_path: str
    severity: Severity
    commit: Optional[str] = None
    rule_id: Optional[str] = None
    line: Optional[int] = None


@dataclass
class DASTFinding:
    alert_name: str
    risk_level: Severity
    url: str
    description: str
    cwe_id: Optional[str] = None
    confidence: Optional[str] = None


@dataclass
class ToolArtifact:
    tool: str
    artifact_type: ArtifactType
    timestamp: str
    scope: str
    status: str
    findings_count: int
    maps_to: list[str] = field(default_factory=list)
    raw_summary: dict = field(default_factory=dict)


@dataclass
class FindingSummary:
    sast: dict = field(default_factory=lambda: {"critical": 0, "high": 0, "medium": 0, "low": 0})
    sca: dict = field(default_factory=lambda: {"critical": 0, "high": 0, "medium": 0, "low": 0})
    secrets: dict = field(default_factory=lambda: {"count": 0, "types": []})
    dast: dict = field(default_factory=lambda: {"critical": 0, "high": 0, "medium": 0, "low": 0})


@dataclass
class CoverageSummary:
    D1_SAST: Verdict = Verdict.NOT_APPLICABLE
    D2_SCA: Verdict = Verdict.NOT_APPLICABLE
    D3_SECRETS: Verdict = Verdict.NOT_APPLICABLE
    D4_DAST: Verdict = Verdict.NOT_APPLICABLE
    D5_REVIEW_GATE: Verdict = Verdict.NOT_APPLICABLE
    D6_BLOCKING_POLICY: Verdict = Verdict.NOT_APPLICABLE
    D7_FINDINGS_TRACKING: Verdict = Verdict.NOT_APPLICABLE
    D8_DEVELOPER_TRAINING: Verdict = Verdict.NOT_APPLICABLE

    def to_dict(self) -> dict:
        return {k: v.value for k, v in asdict(self).items()}


@dataclass
class EvidencePackage:
    evidence_package_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    project: str = ""
    branch: str = ""
    commit_sha: str = ""
    pipeline_run: str = ""
    audit_period: str = ""
    control: str = "DevSecOps"
    standard_references: list[str] = field(default_factory=lambda: ["CYBER/STD/014", "CYBER_062"])
    coverage_summary: CoverageSummary = field(default_factory=CoverageSummary)
    findings_summary: FindingSummary = field(default_factory=FindingSummary)
    blocking_findings: list[dict] = field(default_factory=list)
    gaps: list[str] = field(default_factory=list)
    audit_narrative: str = ""
    artifacts: list[ToolArtifact] = field(default_factory=list)
    signature: Optional[str] = None

    def to_dict(self) -> dict:
        d = asdict(self)
        cs = self.coverage_summary
        if isinstance(cs, CoverageSummary):
            d["coverage_summary"] = cs.to_dict()
        else:
            d["coverage_summary"] = cs if isinstance(cs, dict) else {}
        return d

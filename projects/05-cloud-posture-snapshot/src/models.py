"""Domain models for Cloud Posture Snapshot."""

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional
import uuid
from datetime import datetime, timezone


class CheckStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    NA = "NOT_APPLICABLE"


class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class Provider(str, Enum):
    AWS = "AWS"
    AZURE = "AZURE"
    GCP = "GCP"


@dataclass
class CheckResult:
    check_id: str
    check_title: str
    status: CheckStatus
    severity: Severity
    resource: str
    finding: str
    remediation: str
    vodafone_control: str
    d_statement: str
    cis_section: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        d["status"] = self.status.value
        d["severity"] = self.severity.value
        d["provider"] = getattr(self, "provider", "")
        return d


@dataclass
class PostureSummary:
    total_checks: int = 0
    passed: int = 0
    failed: int = 0
    not_applicable: int = 0
    pass_rate_pct: float = 0.0
    critical_failures: int = 0
    high_failures: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class PostureReport:
    report_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    provider: str = ""
    account_id: str = ""
    region_scope: list[str] = field(default_factory=list)
    cis_benchmark_version: str = ""
    summary: PostureSummary = field(default_factory=PostureSummary)
    findings: list[CheckResult] = field(default_factory=list)
    critical_failures: list[dict] = field(default_factory=list)
    management_summary: str = ""

    def compute_summary(self):
        self.summary = PostureSummary(
            total_checks=len(self.findings),
            passed=sum(1 for f in self.findings if f.status == CheckStatus.PASS),
            failed=sum(1 for f in self.findings if f.status == CheckStatus.FAIL),
            not_applicable=sum(1 for f in self.findings if f.status == CheckStatus.NA),
        )
        if self.summary.total_checks > 0:
            assessed = self.summary.total_checks - self.summary.not_applicable
            self.summary.pass_rate_pct = round(
                (self.summary.passed / assessed * 100) if assessed > 0 else 0, 1
            )
        self.summary.critical_failures = sum(
            1 for f in self.findings
            if f.status == CheckStatus.FAIL and f.severity == Severity.CRITICAL
        )
        self.summary.high_failures = sum(
            1 for f in self.findings
            if f.status == CheckStatus.FAIL and f.severity == Severity.HIGH
        )
        self.critical_failures = [
            f.to_dict() for f in self.findings
            if f.status == CheckStatus.FAIL and f.severity in (Severity.CRITICAL, Severity.HIGH)
        ]

    def rag_status(self) -> str:
        if self.summary.pass_rate_pct >= 80:
            return "GREEN"
        elif self.summary.pass_rate_pct >= 60:
            return "AMBER"
        return "RED"

    def to_dict(self) -> dict:
        d = asdict(self)
        d["summary"] = self.summary.to_dict()
        d["findings"] = [f.to_dict() for f in self.findings]
        d["provider"] = self.provider
        return d

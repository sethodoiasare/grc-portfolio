"""Domain models for Data Classification Scanner."""

from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime, timezone
from typing import Optional


class DataCategory(str, Enum):
    PII = "PII"
    PCI = "PCI"
    PHI = "PHI"
    SECRETS = "SECRETS"
    CUSTOM = "CUSTOM"


class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


# Classification rules with regex patterns
CLASSIFICATION_RULES = [
    # ── PII ───────────────────────────────────────────────────────
    {
        "id": "PII-001",
        "title": "Email Address",
        "category": DataCategory.PII,
        "severity": Severity.MEDIUM,
        "pattern": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "description": "Personal email addresses",
    },
    {
        "id": "PII-002",
        "title": "UK National Insurance Number",
        "category": DataCategory.PII,
        "severity": Severity.HIGH,
        "pattern": r"\b[A-Z]{2}\s?\d{2}\s?\d{2}\s?\d{2}\s?[A-D]\b",
        "description": "UK NINO format: AB 12 34 56 C",
    },
    {
        "id": "PII-003",
        "title": "US Social Security Number",
        "category": DataCategory.PII,
        "severity": Severity.HIGH,
        "pattern": r"\b(?!000|666|9\d{2})\d{3}-(?!00)\d{2}-(?!0000)\d{4}\b",
        "description": "US SSN format: 123-45-6789",
    },
    {
        "id": "PII-004",
        "title": "UK Phone Number",
        "category": DataCategory.PII,
        "severity": Severity.MEDIUM,
        "pattern": r"(?:\+44|0)\s?7\d{3}\s?\d{6}\b",
        "description": "UK mobile numbers",
    },
    {
        "id": "PII-005",
        "title": "UK Passport Number",
        "category": DataCategory.PII,
        "severity": Severity.HIGH,
        "pattern": r"\b[0-9]{9}\b",
        "description": "UK passport number (9 digits)",
    },
    {
        "id": "PII-006",
        "title": "IP Address",
        "category": DataCategory.PII,
        "severity": Severity.LOW,
        "pattern": r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b",
        "description": "IPv4 addresses (may indicate location data)",
    },
    # ── PCI ───────────────────────────────────────────────────────
    {
        "id": "PCI-001",
        "title": "Credit Card Number (Visa/MC/Amex/Discover)",
        "category": DataCategory.PCI,
        "severity": Severity.CRITICAL,
        "pattern": r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})\b",
        "description": "PANs from major card networks",
    },
    {
        "id": "PCI-002",
        "title": "CVV/CVC Number",
        "category": DataCategory.PCI,
        "severity": Severity.CRITICAL,
        "pattern": r"\b[0-9]{3,4}\b",
        "description": "Card verification values (requires context validation)",
    },
    # ── PHI ───────────────────────────────────────────────────────
    {
        "id": "PHI-001",
        "title": "NHS Number",
        "category": DataCategory.PHI,
        "severity": Severity.HIGH,
        "pattern": r"\b\d{3}\s?\d{3}\s?\d{4}\b",
        "description": "UK NHS number format: 123 456 7890",
    },
    # ── Secrets ───────────────────────────────────────────────────
    {
        "id": "SEC-001",
        "title": "AWS Access Key ID",
        "category": DataCategory.SECRETS,
        "severity": Severity.CRITICAL,
        "pattern": r"\bAKIA[0-9A-Z]{16}\b",
        "description": "AWS IAM access key IDs",
    },
    {
        "id": "SEC-002",
        "title": "AWS Secret Access Key",
        "category": DataCategory.SECRETS,
        "severity": Severity.CRITICAL,
        "pattern": r"\b[A-Za-z0-9/+=]{40}\b",
        "description": "AWS secret access keys (high-entropy base64 strings)",
    },
    {
        "id": "SEC-003",
        "title": "Private Key Header",
        "category": DataCategory.SECRETS,
        "severity": Severity.CRITICAL,
        "pattern": r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----",
        "description": "PEM-encoded private key headers",
    },
    {
        "id": "SEC-004",
        "title": "Generic API Key / Token",
        "category": DataCategory.SECRETS,
        "severity": Severity.CRITICAL,
        "pattern": r"\b(?:api[_-]?key|api[_-]?secret|access[_-]?token|auth[_-]?token)\s*[:=]\s*[\'\"][A-Za-z0-9_\-\.]{16,}[\'\"]",
        "description": "API keys and tokens in config files (case-insensitive match)",
    },
    {
        "id": "SEC-005",
        "title": "Connection String",
        "category": DataCategory.SECRETS,
        "severity": Severity.CRITICAL,
        "pattern": r"\b(?:mongodb|postgresql|mysql|redis|jdbc)://[A-Za-z0-9._-]+:[^@\s]+@",
        "description": "Database connection strings with embedded credentials",
    },
]


@dataclass
class ClassificationMatch:
    """A single match found during scanning."""
    rule_id: str
    rule_title: str
    category: DataCategory
    severity: Severity
    match_text: str
    file_path: str
    line_number: int
    context: str = ""  # surrounding text for context

    def to_dict(self) -> dict:
        d = asdict(self)
        d["category"] = self.category.value
        d["severity"] = self.severity.value
        return d


@dataclass
class FileScanResult:
    """Result for a single scanned file."""
    file_path: str
    file_size_bytes: int
    matches: list[ClassificationMatch] = field(default_factory=list)
    error: Optional[str] = None

    @property
    def match_count(self) -> int:
        return len(self.matches)

    def critical_count(self) -> int:
        return sum(1 for m in self.matches if m.severity == Severity.CRITICAL)

    def to_dict(self) -> dict:
        return {
            "file_path": self.file_path,
            "file_size_bytes": self.file_size_bytes,
            "match_count": self.match_count,
            "critical_count": self.critical_count(),
            "matches": [m.to_dict() for m in self.matches],
            "error": self.error,
        }


@dataclass
class ClassificationReport:
    """Complete data classification scan report."""
    report_id: str
    generated_at: str
    scan_root: str
    total_files_scanned: int
    total_matches: int
    files_with_findings: int
    critical_findings: int
    high_findings: int
    medium_findings: int
    low_findings: int
    by_category: dict[str, int] = field(default_factory=dict)
    results: list[FileScanResult] = field(default_factory=list)

    def rag_status(self) -> str:
        if self.critical_findings > 0:
            return "RED"
        if self.high_findings > 5:
            return "AMBER"
        return "GREEN"

    def to_dict(self) -> dict:
        return {
            "report_id": self.report_id,
            "generated_at": self.generated_at,
            "scan_root": self.scan_root,
            "total_files_scanned": self.total_files_scanned,
            "total_matches": self.total_matches,
            "files_with_findings": self.files_with_findings,
            "critical_findings": self.critical_findings,
            "high_findings": self.high_findings,
            "medium_findings": self.medium_findings,
            "low_findings": self.low_findings,
            "rag_status": self.rag_status(),
            "by_category": self.by_category,
            "results": [r.to_dict() for r in self.results],
        }

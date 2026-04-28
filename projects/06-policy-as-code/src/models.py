"""Domain models for Policy-as-Code Starter Kit."""

from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime, timezone
from typing import Optional


class Verdict(str, Enum):
    COMPLIANT = "COMPLIANT"
    NON_COMPLIANT = "NON_COMPLIANT"
    ERROR = "ERROR"


class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


VODAFONE_CONTROLS = {
    "iam": {
        "name": "Management of privileged access rights",
        "d_statement": "D1-D5",
        "standard": "CYBER_038",
    },
    "encryption": {
        "name": "Protection of information in transit and at rest",
        "d_statement": "D1-D17",
        "standard": "CYBER_038",
    },
    "logging": {
        "name": "Security event logging and monitoring",
        "d_statement": "D1-D7",
        "standard": "CYBER_038",
    },
    "networking": {
        "name": "Network security and segregation",
        "d_statement": "D1-D10",
        "standard": "CYBER_038",
    },
}

POLICIES = [
    {
        "id": "IAM-001",
        "title": "IAM Least Privilege — No Wildcard Actions",
        "category": "iam",
        "description": "IAM policies must not contain '*' in Action or Resource elements.",
        "severity": Severity.CRITICAL,
        "rego_file": "iam_least_privilege.rego",
        "remediation": "Replace wildcard actions/resources with explicitly scoped ARNs.",
    },
    {
        "id": "IAM-002",
        "title": "IAM — No Attached Admin Policies",
        "category": "iam",
        "description": "No IAM user or role may have AdministratorAccess policy attached directly.",
        "severity": Severity.CRITICAL,
        "rego_file": "iam_no_admin_policies.rego",
        "remediation": "Remove AdministratorAccess policy and replace with least-privilege custom policies.",
    },
    {
        "id": "IAM-003",
        "title": "IAM — MFA Required for Privileged Users",
        "category": "iam",
        "description": "All IAM users with privileged policies must have MFA enabled.",
        "severity": Severity.HIGH,
        "rego_file": "iam_mfa_required.rego",
        "remediation": "Enable MFA for all privileged IAM users via the AWS console or CLI.",
    },
    {
        "id": "IAM-004",
        "title": "IAM — Access Key Rotation (90 days)",
        "category": "iam",
        "description": "Active access keys must be rotated within 90 days of creation.",
        "severity": Severity.HIGH,
        "rego_file": "iam_key_rotation.rego",
        "remediation": "Rotate access keys via IAM console. Deactivate and delete keys older than 90 days.",
    },
    {
        "id": "ENC-001",
        "title": "Encryption — S3 Buckets Must Use Server-Side Encryption",
        "category": "encryption",
        "description": "All S3 buckets must have default server-side encryption enabled (SSE-S3 or SSE-KMS).",
        "severity": Severity.HIGH,
        "rego_file": "encryption_s3_sse.rego",
        "remediation": "Enable default encryption on S3 buckets via bucket properties > default encryption.",
    },
    {
        "id": "ENC-002",
        "title": "Encryption — EBS Volumes Must Be Encrypted",
        "category": "encryption",
        "description": "All EBS volumes must be encrypted with KMS CMK or AWS-managed keys.",
        "severity": Severity.HIGH,
        "rego_file": "encryption_ebs.rego",
        "remediation": "Enable EBS encryption by default in EC2 console or via account settings API.",
    },
    {
        "id": "ENC-003",
        "title": "Encryption — RDS Instances Must Be Encrypted",
        "category": "encryption",
        "description": "All RDS database instances must have storage encryption enabled.",
        "severity": Severity.HIGH,
        "rego_file": "encryption_rds.rego",
        "remediation": "Modify RDS instance to enable storage encryption (requires recreation if not enabled at creation).",
    },
    {
        "id": "LOG-001",
        "title": "Logging — CloudTrail Must Be Enabled in All Regions",
        "category": "logging",
        "description": "AWS CloudTrail must be configured as a multi-region trail with global service logging.",
        "severity": Severity.HIGH,
        "rego_file": "logging_cloudtrail.rego",
        "remediation": "Create a multi-region CloudTrail trail in the CloudTrail console with global services enabled.",
    },
    {
        "id": "LOG-002",
        "title": "Logging — CloudTrail Log File Validation",
        "category": "logging",
        "description": "CloudTrail trails must have log file validation enabled.",
        "severity": Severity.MEDIUM,
        "rego_file": "logging_log_validation.rego",
        "remediation": "Enable log file validation on existing CloudTrail trails.",
    },
    {
        "id": "LOG-003",
        "title": "Logging — VPC Flow Logs Enabled",
        "category": "logging",
        "description": "VPC flow logs must be enabled for every VPC in the account.",
        "severity": Severity.MEDIUM,
        "rego_file": "logging_vpc_flow_logs.rego",
        "remediation": "Create VPC flow logs for each VPC and publish to CloudWatch Logs or S3.",
    },
    {
        "id": "NET-001",
        "title": "Networking — No Unrestricted SSH (0.0.0.0/0)",
        "category": "networking",
        "description": "Security groups must not allow inbound SSH from 0.0.0.0/0.",
        "severity": Severity.CRITICAL,
        "rego_file": "networking_ssh_restricted.rego",
        "remediation": "Restrict SSH inbound rules to specific IP ranges or use SSM Session Manager.",
    },
    {
        "id": "NET-002",
        "title": "Networking — No Unrestricted RDP (0.0.0.0/0)",
        "category": "networking",
        "description": "Security groups must not allow inbound RDP from 0.0.0.0/0.",
        "severity": Severity.CRITICAL,
        "rego_file": "networking_rdp_restricted.rego",
        "remediation": "Restrict RDP inbound rules to specific IP ranges or use AWS Systems Manager.",
    },
]


@dataclass
class Policy:
    id: str
    title: str
    category: str
    description: str
    severity: Severity
    rego_file: str
    remediation: str

    def to_dict(self) -> dict:
        d = asdict(self)
        d["severity"] = self.severity.value
        return d


@dataclass
class PolicyResult:
    policy_id: str
    policy_title: str
    category: str
    verdict: Verdict
    severity: Severity
    resource: str
    finding: str
    remediation: str
    vodafone_control: str
    d_statement: str

    def to_dict(self) -> dict:
        d = asdict(self)
        d["verdict"] = self.verdict.value
        d["severity"] = self.severity.value
        return d


@dataclass
class PolicyReport:
    report_id: str
    generated_at: str
    engine: str  # "opa" or "python-native"
    total_policies: int
    compliant: int
    non_compliant: int
    errors: int
    results: list[PolicyResult] = field(default_factory=list)

    @property
    def compliance_rate_pct(self) -> float:
        if self.total_policies == 0:
            return 0.0
        return round(self.compliant / self.total_policies * 100, 1)

    def rag_status(self) -> str:
        if self.compliance_rate_pct >= 80:
            return "GREEN"
        elif self.compliance_rate_pct >= 60:
            return "AMBER"
        return "RED"

    def critical_failures(self) -> list[PolicyResult]:
        return [r for r in self.results if r.verdict == Verdict.NON_COMPLIANT and r.severity == Severity.CRITICAL]

    def to_dict(self) -> dict:
        return {
            "report_id": self.report_id,
            "generated_at": self.generated_at,
            "engine": self.engine,
            "total_policies": self.total_policies,
            "compliant": self.compliant,
            "non_compliant": self.non_compliant,
            "errors": self.errors,
            "compliance_rate_pct": self.compliance_rate_pct,
            "rag_status": self.rag_status(),
            "results": [r.to_dict() for r in self.results],
            "critical_failures": [r.to_dict() for r in self.critical_failures()],
        }

"""Pure-Python policy evaluator.

Evaluates policy rules against JSON input without requiring the OPA binary.
Each Rego policy has an equivalent Python implementation for offline demo use.
When OPA is available, the CLI prefers it via subprocess.
"""

from .models import Verdict, Severity, PolicyResult, VODAFONE_CONTROLS


def evaluate(policy: dict, resource: dict) -> PolicyResult:
    """Evaluate a single policy against a single resource input."""
    category = policy["category"]
    vctrl = VODAFONE_CONTROLS.get(category, {"name": "General security control", "d_statement": "D1"})

    handler = _EVALUATORS.get(policy["id"])
    if handler is None:
        return PolicyResult(
            policy_id=policy["id"],
            policy_title=policy["title"],
            category=category,
            verdict=Verdict.ERROR,
            severity=policy["severity"],
            resource=resource.get("ResourceName", resource.get("PolicyName", "unknown")),
            finding=f"No evaluator defined for policy {policy['id']}",
            remediation=policy["remediation"],
            vodafone_control=vctrl["name"],
            d_statement=vctrl["d_statement"],
        )

    compliant, finding_text = handler(resource, policy)
    return PolicyResult(
        policy_id=policy["id"],
        policy_title=policy["title"],
        category=category,
        verdict=Verdict.COMPLIANT if compliant else Verdict.NON_COMPLIANT,
        severity=policy["severity"],
        resource=resource.get("ResourceName", resource.get("PolicyName", resource.get("UserName", resource.get("GroupId", "unknown")))),
        finding=finding_text,
        remediation=policy["remediation"],
        vodafone_control=vctrl["name"],
        d_statement=vctrl["d_statement"],
    )


def _is_wildcarded(value: str) -> bool:
    """Check if a policy value uses an unsafe wildcard.

    Bare '*' or 'service:*' is unsafe. ARNs with '*' in the path
    (e.g. arn:aws:s3:::bucket/*) are scoped and acceptable.
    """
    if value == "*":
        return True
    if value.startswith("arn:"):
        return False
    return "*" in value


# ── Evaluators ───────────────────────────────────────────────────

def _eval_iam_001(resource: dict, policy: dict) -> tuple[bool, str]:
    name = resource.get("PolicyName", "unknown")
    has_wildcard_action = any(_is_wildcarded(a) for a in resource.get("Action", []))
    has_wildcard_resource = any(_is_wildcarded(r) for r in resource.get("Resource", []))
    if has_wildcard_action:
        return False, f"IAM policy '{name}' contains wildcard '*' in Action element"
    if has_wildcard_resource:
        return False, f"IAM policy '{name}' contains wildcard '*' in Resource element"
    return True, f"IAM policy '{name}' uses scoped actions and resources"


def _eval_iam_002(resource: dict, policy: dict) -> tuple[bool, str]:
    name = resource.get("PrincipalName", "unknown")
    admin_pols = {"AdministratorAccess", "PowerUserAccess", "IAMFullAccess"}
    for attached in resource.get("AttachedPolicies", []):
        if attached.get("PolicyName") in admin_pols:
            return False, f"IAM principal '{name}' has admin-level policy '{attached['PolicyName']}' attached directly"
    return True, f"IAM principal '{name}' has no directly attached admin policies"


def _eval_iam_003(resource: dict, policy: dict) -> tuple[bool, str]:
    name = resource.get("UserName", "unknown")
    if not resource.get("MFAEnabled", False):
        return False, f"Privileged IAM user '{name}' does not have MFA enabled"
    return True, f"Privileged IAM user '{name}' has MFA enabled"


def _eval_iam_004(resource: dict, policy: dict) -> tuple[bool, str]:
    name = resource.get("UserName", "unknown")
    key_id = resource.get("AccessKeyId", "unknown")
    age = resource.get("KeyAgeDays", 0)
    if age > 90:
        return False, f"Access key {key_id} for user '{name}' is {age} days old (exceeds 90-day limit)"
    return True, f"Access key {key_id} for user '{name}' is within rotation window ({age} days old)"


def _eval_enc_001(resource: dict, policy: dict) -> tuple[bool, str]:
    name = resource.get("BucketName", "unknown")
    enc = resource.get("DefaultEncryption", {})
    if not enc.get("Enabled", False):
        return False, f"S3 bucket '{name}' does not have default server-side encryption enabled"
    return True, f"S3 bucket '{name}' has default server-side encryption ({enc.get('Algorithm', 'AES256')}) enabled"


def _eval_enc_002(resource: dict, policy: dict) -> tuple[bool, str]:
    vol_id = resource.get("VolumeId", "unknown")
    az = resource.get("AvailabilityZone", "unknown")
    if not resource.get("Encrypted", False):
        return False, f"EBS volume {vol_id} in {az} is not encrypted"
    return True, f"EBS volume {vol_id} in {az} is encrypted with KMS key {resource.get('KmsKeyId', 'default')}"


def _eval_enc_003(resource: dict, policy: dict) -> tuple[bool, str]:
    db_id = resource.get("DBInstanceIdentifier", "unknown")
    if not resource.get("StorageEncrypted", False):
        return False, f"RDS instance '{db_id}' does not have storage encryption enabled"
    return True, f"RDS instance '{db_id}' has storage encryption enabled with KMS key {resource.get('KmsKeyId', 'default')}"


def _eval_log_001(resource: dict, policy: dict) -> tuple[bool, str]:
    name = resource.get("TrailName", "unknown")
    if not resource.get("IsMultiRegionTrail", False):
        return False, f"CloudTrail trail '{name}' is not a multi-region trail"
    if not resource.get("IncludeGlobalServiceEvents", False):
        return False, f"CloudTrail trail '{name}' does not include global service events"
    return True, f"CloudTrail trail '{name}' is multi-region with global service events enabled"


def _eval_log_002(resource: dict, policy: dict) -> tuple[bool, str]:
    name = resource.get("TrailName", "unknown")
    if not resource.get("LogFileValidationEnabled", False):
        return False, f"CloudTrail trail '{name}' does not have log file validation enabled"
    return True, f"CloudTrail trail '{name}' has log file validation enabled"


def _eval_log_003(resource: dict, policy: dict) -> tuple[bool, str]:
    vpc_id = resource.get("VpcId", "unknown")
    if not resource.get("FlowLogsEnabled", False):
        return False, f"VPC {vpc_id} does not have flow logs enabled"
    return True, f"VPC {vpc_id} has flow logs publishing to {resource.get('FlowLogsDestination', 'CloudWatch')}"


def _eval_net_001(resource: dict, policy: dict) -> tuple[bool, str]:
    group_id = resource.get("GroupId", "unknown")
    for rule in resource.get("SecurityGroupRules", []):
        if (rule.get("Protocol") == "tcp" and rule.get("FromPort") == 22
                and rule.get("ToPort") == 22 and rule.get("CidrIp") == "0.0.0.0/0"):
            return False, f"Security group {group_id} allows inbound SSH (port 22) from 0.0.0.0/0"
    return True, f"Security group {group_id} restricts SSH to authorised IP ranges"


def _eval_net_002(resource: dict, policy: dict) -> tuple[bool, str]:
    group_id = resource.get("GroupId", "unknown")
    for rule in resource.get("SecurityGroupRules", []):
        if (rule.get("Protocol") == "tcp" and rule.get("FromPort") == 3389
                and rule.get("ToPort") == 3389 and rule.get("CidrIp") == "0.0.0.0/0"):
            return False, f"Security group {group_id} allows inbound RDP (port 3389) from 0.0.0.0/0"
    return True, f"Security group {group_id} restricts RDP to authorised IP ranges"


_EVALUATORS = {
    "IAM-001": _eval_iam_001,
    "IAM-002": _eval_iam_002,
    "IAM-003": _eval_iam_003,
    "IAM-004": _eval_iam_004,
    "ENC-001": _eval_enc_001,
    "ENC-002": _eval_enc_002,
    "ENC-003": _eval_enc_003,
    "LOG-001": _eval_log_001,
    "LOG-002": _eval_log_002,
    "LOG-003": _eval_log_003,
    "NET-001": _eval_net_001,
    "NET-002": _eval_net_002,
}

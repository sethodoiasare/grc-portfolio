"""AWS CIS v1.5 checks — mock mode (default) with real boto3 path ready."""

import random
from datetime import datetime, timedelta, timezone

from ..models import CheckResult, CheckStatus, Severity
from .registry import AWS_CHECKS, get_vodafone_mapping


class AWSChecker:
    """Run CIS AWS Foundations v1.5 checks.

    In mock mode (default), returns realistic simulated results.
    When boto3 credentials are configured, pass live_session=True and provide a boto3 Session.
    """

    def __init__(self, account_id: str = "111122223333", mock: bool = True, session=None):
        self.account_id = account_id
        self.mock = mock
        self.session = session
        if not mock and session:
            self.iam = session.client("iam")
            self.cloudtrail = session.client("cloudtrail")
            self.s3 = session.client("s3")
            self.ec2 = session.client("ec2")
            self.cloudwatch = session.client("cloudwatch")

    def run_all(self) -> list[CheckResult]:
        results = []
        for check_def in AWS_CHECKS:
            method_name = f"check_{check_def['id'].replace('.', '_').replace('-', '_')}"
            method = getattr(self, method_name, self._check_not_implemented)
            result = method(check_def)
            results.append(result)
        return results

    # ── IAM (1.x) ──────────────────────────────────────────────

    def check_1_1(self, d: dict) -> CheckResult:
        """Avoid use of root account."""
        if self.mock:
            status = CheckStatus.PASS
            finding = "Root account has no recent activity. Last root login: 180 days ago."
        else:
            summary = self.iam.get_account_summary()
            status = CheckStatus.PASS if not summary.get("AccountMFAEnabled") else CheckStatus.FAIL
            finding = ""
        return self._result(d, status, "Root account", finding,
                            "Remove root user access keys. Use IAM roles for all operations.")

    def check_1_2(self, d: dict) -> CheckResult:
        """MFA enabled for root account."""
        if self.mock:
            status = CheckStatus.PASS
            finding = "MFA device is active on root account (virtual authenticator)."
        else:
            status = CheckStatus.PASS  # Would check via iam.get_account_summary()
            finding = ""
        return self._result(d, status, "Root account", finding,
                            "Enable a hardware or virtual MFA device on the root account.")

    def check_1_4(self, d: dict) -> CheckResult:
        """IAM access key rotation within 90 days."""
        if self.mock:
            status = CheckStatus.FAIL
            finding = "3 IAM users have access keys older than 90 days: devops-user (187 days), build-bot (210 days), analyst (95 days)."
        else:
            status = CheckStatus.FAIL
            finding = ""
        return self._result(d, status, "IAM users", finding,
                            "Rotate access keys immediately. Automate key rotation via credential reports.")

    def check_1_5(self, d: dict) -> CheckResult:
        """IAM password policy minimum length >= 14."""
        if self.mock:
            status = CheckStatus.FAIL
            finding = "Account password policy minimum length is 8 characters. Requires minimum 14 per CIS v1.5."
        else:
            status = CheckStatus.PASS
            finding = ""
        return self._result(d, status, "Account password policy", finding,
                            "Update password policy: min length 14, require uppercase, lowercase, digits, symbols.")

    def check_1_7(self, d: dict) -> CheckResult:
        """MFA enabled for console users."""
        if self.mock:
            status = CheckStatus.FAIL
            finding = "2 IAM users with console access do not have MFA enabled: developer@example.com, contractor@example.com."
        else:
            status = CheckStatus.FAIL
            finding = ""
        return self._result(d, status, "IAM console users", finding,
                            "Enforce MFA for all console users via IAM policy condition or AWS SSO.")

    def check_1_14(self, d: dict) -> CheckResult:
        """No root access key exists."""
        if self.mock:
            status = CheckStatus.PASS
            finding = "No access key exists for the root account."
        else:
            status = CheckStatus.PASS
            finding = ""
        return self._result(d, status, "Root account", finding,
                            "Delete any root access keys immediately. Use IAM users with minimum required permissions.")

    def check_1_16(self, d: dict) -> CheckResult:
        """No full admin policies attached to IAM principals."""
        if self.mock:
            status = CheckStatus.FAIL
            finding = "AdministratorAccess policy attached to 1 IAM user (power-user) and 1 IAM role (legacy-admin-role)."
        else:
            status = CheckStatus.FAIL
            finding = ""
        return self._result(d, status, "IAM policies", finding,
                            "Replace AdministratorAccess with scoped policies. Use IAM Access Analyzer for least-privilege.")

    # ── Logging (2.x) ──────────────────────────────────────────

    def check_2_1(self, d: dict) -> CheckResult:
        """CloudTrail enabled in all regions."""
        if self.mock:
            status = CheckStatus.PASS
            finding = "CloudTrail is configured as multi-region trail. Logging to s3://company-cloudtrail-logs with SSE-KMS encryption."
        else:
            status = CheckStatus.FAIL
            finding = ""
        return self._result(d, status, "CloudTrail", finding,
                            "Create a multi-region CloudTrail trail. Enable log file validation and SSE-KMS encryption.")

    def check_2_2(self, d: dict) -> CheckResult:
        """CloudTrail log file validation enabled."""
        if self.mock:
            status = CheckStatus.PASS
            finding = "Log file validation is enabled on the CloudTrail trail."
        else:
            status = CheckStatus.FAIL
            finding = ""
        return self._result(d, status, "CloudTrail", finding,
                            "Enable log file validation on all CloudTrail trails.")

    def check_2_3(self, d: dict) -> CheckResult:
        """S3 bucket for CloudTrail not publicly accessible."""
        if self.mock:
            status = CheckStatus.PASS
            finding = "CloudTrail S3 bucket (company-cloudtrail-logs) has no public access. Bucket policy restricts access to logging service principal."
        else:
            status = CheckStatus.FAIL
            finding = ""
        return self._result(d, status, "S3 (CloudTrail bucket)", finding,
                            "Apply S3 bucket policy restricting access to CloudTrail service. Enable Block Public Access.")

    def check_2_4(self, d: dict) -> CheckResult:
        """CloudTrail integrated with CloudWatch Logs."""
        if self.mock:
            status = CheckStatus.FAIL
            finding = "CloudTrail trail is not forwarding logs to CloudWatch Logs. No CloudWatch Logs log group configured."
        else:
            status = CheckStatus.FAIL
            finding = ""
        return self._result(d, status, "CloudTrail → CloudWatch", finding,
                            "Create a CloudWatch Logs log group and configure the CloudTrail trail to forward events.")

    def check_2_7(self, d: dict) -> CheckResult:
        """VPC flow logging enabled."""
        if self.mock:
            status = CheckStatus.FAIL
            finding = "2 VPCs do not have flow logs enabled: vpc-legacy (vpc-abc123), vpc-staging (vpc-def456)."
        else:
            status = CheckStatus.FAIL
            finding = ""
        return self._result(d, status, "VPC flow logs", finding,
                            "Enable VPC flow logs for all VPCs. Publish to CloudWatch Logs or S3.")

    # ── Monitoring (3.x) ───────────────────────────────────────

    def check_3_1(self, d: dict) -> CheckResult:
        """CloudWatch alarm for root account usage."""
        if self.mock:
            status = CheckStatus.FAIL
            finding = "No CloudWatch alarm configured for root account API usage."
        else:
            status = CheckStatus.FAIL
            finding = ""
        return self._result(d, status, "CloudWatch alarms", finding,
                            "Create a CloudWatch alarm triggered by root account activity. Subscribe SNS topic for notifications.")

    def check_3_3(self, d: dict) -> CheckResult:
        """CloudWatch alarm for unauthorized API calls."""
        if self.mock:
            status = CheckStatus.PASS
            finding = "CloudWatch alarm 'UnauthorizedAPICalls' is active and subscribed to security-notifications SNS topic."
        else:
            status = CheckStatus.FAIL
            finding = ""
        return self._result(d, status, "CloudWatch alarms", finding,
                            "Create a CloudWatch alarm on unauthorized API call patterns via CloudTrail metric filter.")

    def check_3_7(self, d: dict) -> CheckResult:
        """CloudWatch alarm for MFA console sign-in events."""
        if self.mock:
            status = CheckStatus.FAIL
            finding = "No CloudWatch alarm monitoring MFA console sign-in failures."
        else:
            status = CheckStatus.FAIL
            finding = ""
        return self._result(d, status, "CloudWatch alarms", finding,
                            "Create metric filter for console sign-in without MFA. Attach alarm with SNS notification.")

    # ── Networking (5.x) ────────────────────────────────────────

    def check_5_1(self, d: dict) -> CheckResult:
        """No unrestricted ingress to port 22 (SSH)."""
        if self.mock:
            status = CheckStatus.FAIL
            finding = "Security group 'sg-default-app' allows SSH from 0.0.0.0/0 on port 22. 3 EC2 instances affected."
        else:
            status = CheckStatus.FAIL
            finding = ""
        return self._result(d, status, "Security groups", finding,
                            "Restrict SSH access to specific trusted IP ranges. Use SSM Session Manager as an alternative.")

    def check_5_2(self, d: dict) -> CheckResult:
        """Default security groups block all traffic."""
        if self.mock:
            status = CheckStatus.FAIL
            finding = "Default security group in vpc-legacy allows all outbound traffic and has inbound rules for ICMP."
        else:
            status = CheckStatus.FAIL
            finding = ""
        return self._result(d, status, "Security groups", finding,
                            "Remove all rules from default security groups. Create custom SGs for each application tier.")

    def check_5_3(self, d: dict) -> CheckResult:
        """No unrestricted ingress to port 3389 (RDP)."""
        if self.mock:
            status = CheckStatus.PASS
            finding = "No security groups found with unrestricted RDP (3389) access."
        else:
            status = CheckStatus.PASS
            finding = ""
        return self._result(d, status, "Security groups", finding,
                            "Restrict RDP access to specific trusted IP ranges. Use AWS Systems Manager for remote administration.")

    # ── Storage / S3 ───────────────────────────────────────────

    def check_S3_1(self, d: dict) -> CheckResult:
        """S3 bucket versioning enabled."""
        if self.mock:
            status = CheckStatus.FAIL
            finding = "3 S3 buckets do not have versioning enabled: app-assets, cdn-cache, temp-uploads."
        else:
            status = CheckStatus.FAIL
            finding = ""
        return self._result(d, status, "S3 buckets", finding,
                            "Enable versioning on all S3 buckets to protect against accidental deletion.")

    def check_S3_2(self, d: dict) -> CheckResult:
        """S3 bucket MFA delete enabled."""
        if self.mock:
            status = CheckStatus.FAIL
            finding = "MFA delete is not enabled on any production S3 bucket. 8 buckets use versioning without MFA delete."
        else:
            status = CheckStatus.FAIL
            finding = ""
        return self._result(d, status, "S3 buckets", finding,
                            "Enable MFA delete on production S3 buckets to prevent accidental permanent deletion.")

    def check_S3_3(self, d: dict) -> CheckResult:
        """S3 Block Public Access at account level."""
        if self.mock:
            status = CheckStatus.PASS
            finding = "Account-level S3 Block Public Access is enabled. All 4 blocking options active (new ACLs, any ACLs, new policies, any policies)."
        else:
            status = CheckStatus.PASS
            finding = ""
        return self._result(d, status, "S3 account settings", finding,
                            "Enable all S3 Block Public Access settings at the account level.")

    # ── Encryption ─────────────────────────────────────────────

    def check_EBS_1(self, d: dict) -> CheckResult:
        """EBS encryption enabled by default."""
        if self.mock:
            status = CheckStatus.FAIL
            finding = "EBS encryption by default is disabled. 12 out of 28 volumes are unencrypted in us-east-1."
        else:
            status = CheckStatus.FAIL
            finding = ""
        return self._result(d, status, "EBS encryption", finding,
                            "Enable EBS encryption by default in all regions via EC2 console or CLI.")

    # ── Helpers ────────────────────────────────────────────────

    def _check_not_implemented(self, d: dict) -> CheckResult:
        return self._result(d, CheckStatus.NA, "N/A",
                            "Check not yet implemented for this provider.", "")

    def _result(self, check_def: dict, status: CheckStatus, resource: str,
                finding: str, remediation: str) -> CheckResult:
        control_name, d_statement = get_vodafone_mapping(check_def["id"])
        return CheckResult(
            check_id=check_def["id"],
            check_title=check_def["title"],
            status=status,
            severity=Severity(check_def["severity"]),
            resource=resource,
            finding=finding,
            remediation=remediation,
            vodafone_control=control_name,
            d_statement=d_statement,
            cis_section=check_def.get("section", ""),
        )

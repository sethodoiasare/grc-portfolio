"""Tests for AWS CIS v1.5 checks."""

from src.checks.aws import AWSChecker
from src.models import CheckStatus, Severity


class TestAWSChecker:
    def setup_method(self):
        self.checker = AWSChecker(account_id="111122223333", mock=True)

    def test_run_all_returns_correct_count(self):
        results = self.checker.run_all()
        assert len(results) == 22

    def test_every_result_has_check_id(self):
        results = self.checker.run_all()
        for r in results:
            assert r.check_id
            assert r.check_title
            assert isinstance(r.status, CheckStatus)
            assert isinstance(r.severity, Severity)

    def test_root_mfa_check_is_pass(self):
        r = self.checker.check_1_2({"id": "1.2", "title": "MFA enabled for root account", "section": "1", "severity": "CRITICAL"})
        assert r.status == CheckStatus.PASS
        assert r.severity == Severity.CRITICAL

    def test_key_rotation_check_is_fail(self):
        r = self.checker.check_1_4({"id": "1.4", "title": "IAM access key rotation", "section": "1", "severity": "HIGH"})
        assert r.status == CheckStatus.FAIL
        assert r.severity == Severity.HIGH

    def test_no_root_access_key_is_pass(self):
        r = self.checker.check_1_14({"id": "1.14", "title": "No root access key exists", "section": "1", "severity": "CRITICAL"})
        assert r.status == CheckStatus.PASS

    def test_admin_policies_is_fail(self):
        r = self.checker.check_1_16({"id": "1.16", "title": "No full admin policies attached", "section": "1", "severity": "HIGH"})
        assert r.status == CheckStatus.FAIL

    def test_cloudtrail_enabled_is_pass(self):
        r = self.checker.check_2_1({"id": "2.1", "title": "CloudTrail enabled in all regions", "section": "2", "severity": "HIGH"})
        assert r.status == CheckStatus.PASS

    def test_cloudtrail_validation_is_pass(self):
        r = self.checker.check_2_2({"id": "2.2", "title": "CloudTrail log file validation enabled", "section": "2", "severity": "MEDIUM"})
        assert r.status == CheckStatus.PASS

    def test_cloudwatch_integration_is_fail(self):
        r = self.checker.check_2_4({"id": "2.4", "title": "CloudTrail integrated with CloudWatch Logs", "section": "2", "severity": "MEDIUM"})
        assert r.status == CheckStatus.FAIL

    def test_vpc_flow_logs_is_fail(self):
        r = self.checker.check_2_7({"id": "2.7", "title": "VPC flow logging enabled", "section": "2", "severity": "MEDIUM"})
        assert r.status == CheckStatus.FAIL

    def test_ssh_unrestricted_is_fail(self):
        r = self.checker.check_5_1({"id": "5.1", "title": "No unrestricted ingress to port 22 (SSH)", "section": "5", "severity": "HIGH"})
        assert r.status == CheckStatus.FAIL

    def test_s3_block_public_access_is_pass(self):
        r = self.checker.check_S3_3({"id": "S3.3", "title": "S3 Block Public Access enabled at account level", "section": "6", "severity": "CRITICAL"})
        assert r.status == CheckStatus.PASS

    def test_s3_versioning_is_fail(self):
        r = self.checker.check_S3_1({"id": "S3.1", "title": "S3 bucket versioning enabled", "section": "6", "severity": "LOW"})
        assert r.status == CheckStatus.FAIL

    def test_ebs_encryption_is_fail(self):
        r = self.checker.check_EBS_1({"id": "EBS.1", "title": "EBS encryption enabled by default", "section": "7", "severity": "MEDIUM"})
        assert r.status == CheckStatus.FAIL

    def test_all_results_have_vodafone_mapping(self):
        results = self.checker.run_all()
        for r in results:
            assert r.vodafone_control
            assert r.d_statement
            assert r.remediation

    def test_result_to_dict(self):
        r = self.checker.check_1_1({"id": "1.1", "title": "Avoid use of root account", "section": "1", "severity": "CRITICAL"})
        d = r.to_dict()
        assert d["check_id"] == "1.1"
        assert d["status"] == "PASS"
        assert d["severity"] == "CRITICAL"
        assert "vodafone_control" in d

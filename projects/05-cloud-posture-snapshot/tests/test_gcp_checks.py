"""Tests for GCP CIS v2.0 checks."""

from src.checks.gcp import GCPChecker
from src.models import CheckStatus, Severity


class TestGCPChecker:
    def setup_method(self):
        self.checker = GCPChecker(project_id="test-gcp-project", mock=True)

    def test_run_all_returns_correct_count(self):
        results = self.checker.run_all()
        assert len(results) == 14

    def test_service_account_admin_is_fail(self):
        r = self.checker.check_1_1({"id": "1.1", "title": "No service account has admin privileges", "section": "1", "severity": "CRITICAL"})
        assert r.status == CheckStatus.FAIL

    def test_key_rotation_is_fail(self):
        r = self.checker.check_1_4({"id": "1.4", "title": "Service account key rotation (max 90 days)", "section": "1", "severity": "HIGH"})
        assert r.status == CheckStatus.FAIL

    def test_user_managed_keys_is_fail(self):
        r = self.checker.check_1_6({"id": "1.6", "title": "No user-managed keys for Google-managed service accounts", "section": "1", "severity": "MEDIUM"})
        assert r.status == CheckStatus.FAIL

    def test_api_keys_is_pass(self):
        r = self.checker.check_1_7({"id": "1.7", "title": "API keys not in use", "section": "1", "severity": "HIGH"})
        assert r.status == CheckStatus.PASS

    def test_audit_logs_is_pass(self):
        r = self.checker.check_2_1({"id": "2.1", "title": "Cloud Audit Logs enabled for all services", "section": "2", "severity": "HIGH"})
        assert r.status == CheckStatus.PASS

    def test_log_sinks_is_pass(self):
        r = self.checker.check_2_2({"id": "2.2", "title": "Log sinks configured for all log entries", "section": "2", "severity": "MEDIUM"})
        assert r.status == CheckStatus.PASS

    def test_default_ssh_is_fail(self):
        r = self.checker.check_3_1({"id": "3.1", "title": "Default VPC firewall — no open SSH (22)", "section": "3", "severity": "HIGH"})
        assert r.status == CheckStatus.FAIL

    def test_default_rdp_is_pass(self):
        r = self.checker.check_3_2({"id": "3.2", "title": "Default VPC firewall — no open RDP (3389)", "section": "3", "severity": "HIGH"})
        assert r.status == CheckStatus.PASS

    def test_all_ports_is_fail(self):
        r = self.checker.check_3_3({"id": "3.3", "title": "No firewall rules with 0.0.0.0/0 on all ports", "section": "3", "severity": "CRITICAL"})
        assert r.status == CheckStatus.FAIL

    def test_flow_logs_is_fail(self):
        r = self.checker.check_3_6({"id": "3.6", "title": "VPC flow logging enabled", "section": "8", "severity": "MEDIUM"})
        assert r.status == CheckStatus.FAIL

    def test_public_buckets_is_fail(self):
        r = self.checker.check_4_1({"id": "4.1", "title": "Cloud Storage buckets not publicly accessible", "section": "6", "severity": "CRITICAL"})
        assert r.status == CheckStatus.FAIL

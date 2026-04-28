"""Tests for Azure CIS v2.0 checks."""

from src.checks.azure import AzureChecker
from src.models import CheckStatus, Severity


class TestAzureChecker:
    def setup_method(self):
        self.checker = AzureChecker(subscription_id="test-sub-id", mock=True)

    def test_run_all_returns_correct_count(self):
        results = self.checker.run_all()
        assert len(results) == 16

    def test_owner_mfa_is_fail(self):
        r = self.checker.check_1_1({"id": "1.1", "title": "MFA for all users with owner role", "section": "1", "severity": "CRITICAL"})
        assert r.status == CheckStatus.FAIL
        assert r.severity == Severity.CRITICAL

    def test_all_users_mfa_is_fail(self):
        r = self.checker.check_1_2({"id": "1.2", "title": "MFA for all users in subscription", "section": "1", "severity": "HIGH"})
        assert r.status == CheckStatus.FAIL

    def test_guest_review_is_pass(self):
        r = self.checker.check_1_5({"id": "1.5", "title": "Guest users reviewed within 30 days", "section": "1", "severity": "MEDIUM"})
        assert r.status == CheckStatus.PASS

    def test_defender_servers_is_pass(self):
        r = self.checker.check_2_1({"id": "2.1", "title": "Defender for Cloud — Servers plan enabled", "section": "4", "severity": "HIGH"})
        assert r.status == CheckStatus.PASS

    def test_defender_storage_is_fail(self):
        r = self.checker.check_2_3({"id": "2.3", "title": "Defender for Cloud — Storage plan enabled", "section": "4", "severity": "MEDIUM"})
        assert r.status == CheckStatus.FAIL

    def test_secure_transfer_is_fail(self):
        r = self.checker.check_3_1({"id": "3.1", "title": "Storage accounts require secure transfer (HTTPS)", "section": "6", "severity": "HIGH"})
        assert r.status == CheckStatus.FAIL

    def test_public_blob_is_fail(self):
        r = self.checker.check_3_7({"id": "3.7", "title": "Storage accounts public blob access disabled", "section": "6", "severity": "CRITICAL"})
        assert r.status == CheckStatus.FAIL

    def test_sql_auditing_is_pass(self):
        r = self.checker.check_4_1({"id": "4.1", "title": "SQL server auditing enabled", "section": "2", "severity": "MEDIUM"})
        assert r.status == CheckStatus.PASS

    def test_ssh_nsg_is_fail(self):
        r = self.checker.check_6_2({"id": "6.2", "title": "SSH not open from internet (NSG rule)", "section": "5", "severity": "HIGH"})
        assert r.status == CheckStatus.FAIL

    def test_rdp_nsg_is_pass(self):
        r = self.checker.check_6_1({"id": "6.1", "title": "RDP not open from internet (NSG rule)", "section": "5", "severity": "HIGH"})
        assert r.status == CheckStatus.PASS

    def test_disk_encryption_is_fail(self):
        r = self.checker.check_ENC_1({"id": "ENC.1", "title": "Azure Disk Encryption enabled for VMs", "section": "7", "severity": "MEDIUM"})
        assert r.status == CheckStatus.FAIL

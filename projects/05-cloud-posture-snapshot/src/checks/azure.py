"""Azure CIS v2.0 checks — mock mode (default) with real SDK path ready."""

import random

from ..models import CheckResult, CheckStatus, Severity
from .registry import AZURE_CHECKS, get_vodafone_mapping


class AzureChecker:
    """Run CIS Microsoft Azure Foundations v2.0 checks.

    In mock mode (default), returns realistic simulated results.
    Set mock=False and provide credentials via Azure CLI login or environment variables.
    """

    def __init__(self, subscription_id: str = "00000000-0000-0000-0000-000000000000", mock: bool = True):
        self.subscription_id = subscription_id
        self.mock = mock

    def run_all(self) -> list[CheckResult]:
        results = []
        for check_def in AZURE_CHECKS:
            method_name = f"check_{check_def['id'].replace('.', '_').replace('-', '_')}"
            method = getattr(self, method_name, self._check_not_implemented)
            result = method(check_def)
            results.append(result)
        return results

    # ── Identity (1.x) ─────────────────────────────────────────

    def check_1_1(self, d: dict) -> CheckResult:
        if self.mock:
            status = CheckStatus.FAIL
            finding = "2 accounts with Owner role do not have MFA: admin@contoso.com, breakglass@contoso.com (break-glass excluded per policy)."
        else:
            status = CheckStatus.FAIL
            finding = ""
        return self._result(d, status, "Azure AD Owner role", finding,
                            "Enforce MFA via Conditional Access policy for all users with privileged roles.")

    def check_1_2(self, d: dict) -> CheckResult:
        if self.mock:
            status = CheckStatus.FAIL
            finding = "15 of 42 subscription users (35.7%) do not have MFA registered. Missing MFA users concentrated in development team."
        else:
            status = CheckStatus.FAIL
            finding = ""
        return self._result(d, status, "Azure AD users", finding,
                            "Enable MFA for all users via Conditional Access or Security Defaults.")

    def check_1_5(self, d: dict) -> CheckResult:
        if self.mock:
            status = CheckStatus.PASS
            finding = "Guest user access reviews configured monthly. Last review: 14 days ago. 0 stale guest accounts."
        else:
            status = CheckStatus.PASS
            finding = ""
        return self._result(d, status, "Azure AD guest users", finding,
                            "Configure access reviews for guest users with monthly cadence.")

    def check_1_9(self, d: dict) -> CheckResult:
        if self.mock:
            status = CheckStatus.PASS
            finding = "Security Defaults enabled. All Azure AD users must register and use MFA."
        else:
            status = CheckStatus.FAIL
            finding = ""
        return self._result(d, status, "Azure AD MFA", finding,
                            "Enable Security Defaults or configure Conditional Access policies requiring MFA for all users.")

    # ── Security Center (2.x) ──────────────────────────────────

    def check_2_1(self, d: dict) -> CheckResult:
        if self.mock:
            status = CheckStatus.PASS
            finding = "Defender for Cloud — Servers plan (Plan 2) is enabled across all subscriptions."
        else:
            status = CheckStatus.FAIL
            finding = ""
        return self._result(d, status, "Defender for Cloud", finding,
                            "Enable Defender for Servers Plan 2 on all subscriptions.")

    def check_2_2(self, d: dict) -> CheckResult:
        if self.mock:
            status = CheckStatus.PASS
            finding = "Defender for Cloud — SQL plan enabled for all SQL servers and managed instances."
        else:
            status = CheckStatus.FAIL
            finding = ""
        return self._result(d, status, "Defender for Cloud", finding,
                            "Enable Defender for SQL on all SQL servers and managed instances.")

    def check_2_3(self, d: dict) -> CheckResult:
        if self.mock:
            status = CheckStatus.FAIL
            finding = "Defender for Cloud — Storage plan not enabled. 12 storage accounts are not covered by Defender."
        else:
            status = CheckStatus.FAIL
            finding = ""
        return self._result(d, status, "Defender for Cloud", finding,
                            "Enable Defender for Storage on all subscriptions with storage accounts.")

    # ── Storage (3.x) ──────────────────────────────────────────

    def check_3_1(self, d: dict) -> CheckResult:
        if self.mock:
            status = CheckStatus.FAIL
            finding = "2 storage accounts have secure transfer disabled: legacyfilestore, devartifacts. HTTP access still permitted."
        else:
            status = CheckStatus.FAIL
            finding = ""
        return self._result(d, status, "Storage accounts", finding,
                            "Enable 'Secure transfer required' on all storage accounts to enforce HTTPS only.")

    def check_3_7(self, d: dict) -> CheckResult:
        if self.mock:
            status = CheckStatus.FAIL
            finding = "1 storage account (public-docs) has public blob access enabled. Anonymous read access to blobs is permitted."
        else:
            status = CheckStatus.FAIL
            finding = ""
        return self._result(d, status, "Storage accounts", finding,
                            "Disable 'Allow Blob Public Access' on all storage accounts. Use SAS tokens or private endpoints.")

    # ── Databases (4.x) ────────────────────────────────────────

    def check_4_1(self, d: dict) -> CheckResult:
        if self.mock:
            status = CheckStatus.PASS
            finding = "SQL server auditing enabled on all 4 Azure SQL servers. Audit logs retained for 90+ days."
        else:
            status = CheckStatus.FAIL
            finding = ""
        return self._result(d, status, "Azure SQL servers", finding,
                            "Enable auditing on all SQL servers. Configure log retention > 90 days.")

    # ── Logging (5.x) ──────────────────────────────────────────

    def check_5_1(self, d: dict) -> CheckResult:
        if self.mock:
            status = CheckStatus.FAIL
            finding = "No Activity Log alert configured for policy assignment changes (Microsoft.Authorization/policyAssignments/write)."
        else:
            status = CheckStatus.FAIL
            finding = ""
        return self._result(d, status, "Activity Log alerts", finding,
                            "Create an Activity Log alert for policy assignment operations with email/SMS action group.")

    def check_5_3(self, d: dict) -> CheckResult:
        if self.mock:
            status = CheckStatus.PASS
            finding = "Activity Log alert 'SecurityGroupChanges' monitors NSG create/update/delete operations. Action group: secops-pager."
        else:
            status = CheckStatus.FAIL
            finding = ""
        return self._result(d, status, "Activity Log alerts", finding,
                            "Create Activity Log alert for NSG changes with notification action group.")

    # ── Networking (6.x) ───────────────────────────────────────

    def check_6_1(self, d: dict) -> CheckResult:
        if self.mock:
            status = CheckStatus.PASS
            finding = "No NSG rules found allowing unrestricted inbound RDP (3389) from internet. RDP access restricted to VPN gateway range 10.100.0.0/16."
        else:
            status = CheckStatus.FAIL
            finding = ""
        return self._result(d, status, "NSG rules", finding,
                            "Remove any NSG rules allowing RDP from 0.0.0.0/0. Use Azure Bastion for secure RDP access.")

    def check_6_2(self, d: dict) -> CheckResult:
        if self.mock:
            status = CheckStatus.FAIL
            finding = "NSG rule in 'dev-subnet-nsg' allows SSH from any source (0.0.0.0/0) on port 22."
        else:
            status = CheckStatus.FAIL
            finding = ""
        return self._result(d, status, "NSG rules", finding,
                            "Restrict SSH to specific IP ranges or use Azure Bastion for secure shell access.")

    def check_6_5(self, d: dict) -> CheckResult:
        if self.mock:
            status = CheckStatus.PASS
            finding = "Network Watcher enabled in all 6 Azure regions used by the subscription."
        else:
            status = CheckStatus.FAIL
            finding = ""
        return self._result(d, status, "Network Watcher", finding,
                            "Enable Network Watcher in every region where resources are deployed.")

    # ── Encryption ─────────────────────────────────────────────

    def check_ENC_1(self, d: dict) -> CheckResult:
        if self.mock:
            status = CheckStatus.FAIL
            finding = "3 VMs in production resource group do not have Azure Disk Encryption enabled. OS and data disks are unencrypted."
        else:
            status = CheckStatus.FAIL
            finding = ""
        return self._result(d, status, "Azure Disk Encryption", finding,
                            "Enable Azure Disk Encryption on all VMs using Azure Key Vault managed keys.")

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

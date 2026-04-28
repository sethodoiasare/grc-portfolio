"""Tests for the Python policy evaluator."""

import pytest
from src.models import POLICIES, Verdict, Severity
from src.evaluator import evaluate


def _find_policy(policy_id: str) -> dict:
    for p in POLICIES:
        if p["id"] == policy_id:
            return p
    raise ValueError(f"Policy {policy_id} not found")


class TestIAM001LeastPrivilege:
    def test_compliant_when_no_wildcards(self):
        r = evaluate(_find_policy("IAM-001"), {
            "PolicyName": "S3ReadOnly",
            "Action": ["s3:GetObject"],
            "Resource": ["arn:aws:s3:::bucket/*"],
        })
        assert r.verdict == Verdict.COMPLIANT

    def test_non_compliant_when_wildcard_action(self):
        r = evaluate(_find_policy("IAM-001"), {
            "PolicyName": "BadPolicy",
            "Action": ["s3:*"],
            "Resource": ["arn:aws:s3:::bucket/*"],
        })
        assert r.verdict == Verdict.NON_COMPLIANT
        assert "wildcard" in r.finding.lower()

    def test_non_compliant_when_wildcard_resource(self):
        r = evaluate(_find_policy("IAM-001"), {
            "PolicyName": "BadPolicy",
            "Action": ["s3:GetObject"],
            "Resource": ["*"],
        })
        assert r.verdict == Verdict.NON_COMPLIANT

    def test_vodafone_control_mapped(self):
        r = evaluate(_find_policy("IAM-001"), {
            "PolicyName": "Test", "Action": ["s3:GetObject"], "Resource": ["arn:..."],
        })
        assert "privileged" in r.vodafone_control.lower()


class TestIAM002NoAdminPolicies:
    def test_compliant_no_admin(self):
        r = evaluate(_find_policy("IAM-002"), {
            "PrincipalName": "alice",
            "AttachedPolicies": [{"PolicyName": "ReadOnlyAccess"}],
        })
        assert r.verdict == Verdict.COMPLIANT

    def test_non_compliant_admin_attached(self):
        r = evaluate(_find_policy("IAM-002"), {
            "PrincipalName": "bob",
            "AttachedPolicies": [{"PolicyName": "AdministratorAccess"}],
        })
        assert r.verdict == Verdict.NON_COMPLIANT
        assert "AdministratorAccess" in r.finding

    def test_non_compliant_iam_full_access(self):
        r = evaluate(_find_policy("IAM-002"), {
            "PrincipalName": "carol",
            "AttachedPolicies": [{"PolicyName": "IAMFullAccess"}],
        })
        assert r.verdict == Verdict.NON_COMPLIANT


class TestIAM003MFARequired:
    def test_compliant_with_mfa(self):
        r = evaluate(_find_policy("IAM-003"), {"UserName": "alice", "MFAEnabled": True})
        assert r.verdict == Verdict.COMPLIANT

    def test_non_compliant_without_mfa(self):
        r = evaluate(_find_policy("IAM-003"), {"UserName": "bob", "MFAEnabled": False})
        assert r.verdict == Verdict.NON_COMPLIANT


class TestIAM004KeyRotation:
    def test_compliant_within_90_days(self):
        r = evaluate(_find_policy("IAM-004"), {"UserName": "alice", "AccessKeyId": "AKIA1234", "KeyAgeDays": 45})
        assert r.verdict == Verdict.COMPLIANT

    def test_non_compliant_over_90_days(self):
        r = evaluate(_find_policy("IAM-004"), {"UserName": "bob", "AccessKeyId": "AKIA5678", "KeyAgeDays": 120})
        assert r.verdict == Verdict.NON_COMPLIANT

    def test_exactly_90_days_is_compliant(self):
        r = evaluate(_find_policy("IAM-004"), {"UserName": "carol", "AccessKeyId": "AKIA9999", "KeyAgeDays": 90})
        assert r.verdict == Verdict.COMPLIANT


class TestENC001S3SSE:
    def test_compliant_with_encryption(self):
        r = evaluate(_find_policy("ENC-001"), {
            "BucketName": "secure", "DefaultEncryption": {"Enabled": True, "Algorithm": "AES256"},
        })
        assert r.verdict == Verdict.COMPLIANT

    def test_non_compliant_without_encryption(self):
        r = evaluate(_find_policy("ENC-001"), {
            "BucketName": "insecure", "DefaultEncryption": {"Enabled": False},
        })
        assert r.verdict == Verdict.NON_COMPLIANT


class TestENC002EBS:
    def test_compliant_encrypted(self):
        r = evaluate(_find_policy("ENC-002"), {"VolumeId": "vol-1", "AvailabilityZone": "eu-west-1a", "Encrypted": True})
        assert r.verdict == Verdict.COMPLIANT

    def test_non_compliant_unencrypted(self):
        r = evaluate(_find_policy("ENC-002"), {"VolumeId": "vol-2", "AvailabilityZone": "eu-west-1b", "Encrypted": False})
        assert r.verdict == Verdict.NON_COMPLIANT


class TestENC003RDS:
    def test_compliant_encrypted(self):
        r = evaluate(_find_policy("ENC-003"), {"DBInstanceIdentifier": "db1", "StorageEncrypted": True})
        assert r.verdict == Verdict.COMPLIANT

    def test_non_compliant_unencrypted(self):
        r = evaluate(_find_policy("ENC-003"), {"DBInstanceIdentifier": "db2", "StorageEncrypted": False})
        assert r.verdict == Verdict.NON_COMPLIANT


class TestLOG001CloudTrail:
    def test_compliant_multi_region(self):
        r = evaluate(_find_policy("LOG-001"), {
            "TrailName": "main", "IsMultiRegionTrail": True, "IncludeGlobalServiceEvents": True,
        })
        assert r.verdict == Verdict.COMPLIANT

    def test_non_compliant_single_region(self):
        r = evaluate(_find_policy("LOG-001"), {
            "TrailName": "old", "IsMultiRegionTrail": False, "IncludeGlobalServiceEvents": False,
        })
        assert r.verdict == Verdict.NON_COMPLIANT

    def test_non_compliant_no_global_services(self):
        r = evaluate(_find_policy("LOG-001"), {
            "TrailName": "partial", "IsMultiRegionTrail": True, "IncludeGlobalServiceEvents": False,
        })
        assert r.verdict == Verdict.NON_COMPLIANT


class TestLOG002LogValidation:
    def test_compliant_validation_enabled(self):
        r = evaluate(_find_policy("LOG-002"), {"TrailName": "main", "LogFileValidationEnabled": True})
        assert r.verdict == Verdict.COMPLIANT

    def test_non_compliant_validation_disabled(self):
        r = evaluate(_find_policy("LOG-002"), {"TrailName": "old", "LogFileValidationEnabled": False})
        assert r.verdict == Verdict.NON_COMPLIANT


class TestLOG003VPCFlowLogs:
    def test_compliant_flow_logs_enabled(self):
        r = evaluate(_find_policy("LOG-003"), {"VpcId": "vpc-1", "FlowLogsEnabled": True})
        assert r.verdict == Verdict.COMPLIANT

    def test_non_compliant_flow_logs_disabled(self):
        r = evaluate(_find_policy("LOG-003"), {"VpcId": "vpc-2", "FlowLogsEnabled": False})
        assert r.verdict == Verdict.NON_COMPLIANT


class TestNET001SSHRestricted:
    def test_compliant_ssh_restricted(self):
        r = evaluate(_find_policy("NET-001"), {
            "GroupId": "sg-1",
            "SecurityGroupRules": [{"Protocol": "tcp", "FromPort": 22, "ToPort": 22, "CidrIp": "10.0.0.0/8"}],
        })
        assert r.verdict == Verdict.COMPLIANT

    def test_non_compliant_ssh_open(self):
        r = evaluate(_find_policy("NET-001"), {
            "GroupId": "sg-2",
            "SecurityGroupRules": [{"Protocol": "tcp", "FromPort": 22, "ToPort": 22, "CidrIp": "0.0.0.0/0"}],
        })
        assert r.verdict == Verdict.NON_COMPLIANT

    def test_no_rules_is_compliant(self):
        r = evaluate(_find_policy("NET-001"), {"GroupId": "sg-3", "SecurityGroupRules": []})
        assert r.verdict == Verdict.COMPLIANT


class TestNET002RDPRestricted:
    def test_compliant_rdp_restricted(self):
        r = evaluate(_find_policy("NET-002"), {
            "GroupId": "sg-1",
            "SecurityGroupRules": [{"Protocol": "tcp", "FromPort": 3389, "ToPort": 3389, "CidrIp": "10.0.0.0/8"}],
        })
        assert r.verdict == Verdict.COMPLIANT

    def test_non_compliant_rdp_open(self):
        r = evaluate(_find_policy("NET-002"), {
            "GroupId": "sg-2",
            "SecurityGroupRules": [{"Protocol": "tcp", "FromPort": 3389, "ToPort": 3389, "CidrIp": "0.0.0.0/0"}],
        })
        assert r.verdict == Verdict.NON_COMPLIANT

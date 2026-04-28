"""Tests for scanner orchestration and report generation."""

import json
from src.scanner import scan
from src.models import PolicyReport, Verdict


class TestScan:
    def test_returns_policy_report(self):
        report = scan([{"_policy_id": "IAM-001", "PolicyName": "Test", "Action": ["s3:*"], "Resource": ["*"]}])
        assert isinstance(report, PolicyReport)
        assert report.engine == "python-native"

    def test_total_matches_input_resources(self):
        input_data = [
            {"_policy_id": "IAM-001", "PolicyName": "P1", "Action": ["s3:GetObject"], "Resource": ["arn:..."]},
            {"_policy_id": "IAM-003", "UserName": "alice", "MFAEnabled": True},
        ]
        report = scan(input_data)
        assert report.total_policies == 2

    def test_counts_compliant_and_non_compliant(self):
        input_data = [
            {"_policy_id": "IAM-001", "PolicyName": "Good", "Action": ["s3:GetObject"], "Resource": ["arn:..."]},
            {"_policy_id": "IAM-001", "PolicyName": "Bad", "Action": ["*"], "Resource": ["*"]},
        ]
        report = scan(input_data)
        assert report.compliant == 1
        assert report.non_compliant == 1

    def test_compliance_rate_pct(self):
        input_data = [
            {"_policy_id": "IAM-003", "UserName": "a", "MFAEnabled": True},
            {"_policy_id": "IAM-003", "UserName": "b", "MFAEnabled": False},
        ]
        report = scan(input_data)
        assert report.compliance_rate_pct == 50.0

    def test_rag_green(self):
        input_data = [
            {"_policy_id": "IAM-003", "UserName": "alice", "MFAEnabled": True},
            {"_policy_id": "IAM-001", "PolicyName": "secure", "Action": ["s3:GetObject"], "Resource": ["arn:..."]},
            {"_policy_id": "ENC-001", "BucketName": "secure", "DefaultEncryption": {"Enabled": True, "Algorithm": "AES256"}},
        ]
        report = scan(input_data)
        assert report.rag_status() == "GREEN"

    def test_rag_red(self):
        input_data = [
            {"_policy_id": "IAM-003", "UserName": "bob", "MFAEnabled": False},
            {"_policy_id": "IAM-001", "PolicyName": "Bad", "Action": ["*"], "Resource": ["*"]},
        ]
        report = scan(input_data)
        assert report.rag_status() == "RED"

    def test_critical_failures(self):
        input_data = [{
            "_policy_id": "NET-001", "GroupId": "sg-bad", "SecurityGroupRules": [
                {"Protocol": "tcp", "FromPort": 22, "ToPort": 22, "CidrIp": "0.0.0.0/0"},
            ],
        }]
        report = scan(input_data)
        crit = report.critical_failures()
        assert len(crit) == 1
        assert crit[0].severity.value == "CRITICAL"

    def test_demo_data_runs(self):
        from src.cli import _demo_data
        report = scan(_demo_data())
        assert report.total_policies == 24  # 12 policies x 2 resources each
        assert report.compliant > 0
        assert report.non_compliant > 0

    def test_to_dict_serializable(self):
        input_data = [
            {"_policy_id": "IAM-001", "PolicyName": "Test", "Action": ["s3:GetObject"], "Resource": ["arn:..."]},
        ]
        report = scan(input_data)
        d = report.to_dict()
        assert isinstance(d["results"], list)
        json.dumps(d)

    def test_subset_policies(self):
        input_data = _full_demo()
        report = scan(input_data, policy_ids=["IAM-003"])
        assert report.total_policies == 2
        assert all(r.policy_id == "IAM-003" for r in report.results)

    def test_empty_input_returns_empty_report(self):
        report = scan([])
        assert report.total_policies == 0
        assert report.compliant == 0
        assert report.non_compliant == 0


def _full_demo():
    from src.cli import _demo_data
    return _demo_data()

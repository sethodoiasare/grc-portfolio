"""CLI for Policy-as-Code Starter Kit."""

import argparse
import sys
import json
from pathlib import Path

from .models import POLICIES
from .scanner import scan


def main():
    parser = argparse.ArgumentParser(
        prog="policy-as-code",
        description="Policy-as-Code Starter Kit — OPA/Rego policies for IAM, encryption, logging",
    )
    sub = parser.add_subparsers(dest="command")

    scan_p = sub.add_parser("scan", help="Evaluate policies against input data")
    scan_p.add_argument("--input", "-i", type=Path, help="JSON file with resources to evaluate")
    scan_p.add_argument("--policy", "-p", action="append", help="Run specific policy ID (repeatable)")
    scan_p.add_argument("--output", "-o", type=Path, default=Path("policy-report.json"), help="Output path")
    scan_p.add_argument("--demo", action="store_true", help="Run against built-in demo data")

    list_p = sub.add_parser("list-policies", help="List all available policies")
    list_p.add_argument("--category", "-c", choices=["iam", "encryption", "logging", "networking"],
                        help="Filter by category")

    args = parser.parse_args()

    if args.command == "scan":
        if args.demo:
            input_data = _demo_data()
        elif args.input:
            input_data = json.loads(args.input.read_text())
        else:
            print("Error: --input or --demo required")
            sys.exit(1)

        from .reporter import export_json
        report = scan(input_data, args.policy)
        path = export_json(report, args.output)
        _print_summary(report)
        print(f"\nReport saved to {path}")

    elif args.command == "list-policies":
        policies = POLICIES
        if args.category:
            policies = [p for p in policies if p["category"] == args.category]
        print(f"\n{'ID':<10} {'Category':<14} {'Severity':<10} Title")
        print("-" * 80)
        for p in policies:
            print(f"{p['id']:<10} {p['category']:<14} {p['severity'].value:<10} {p['title']}")
        print(f"\n{policies.__len__()} policies listed.")

    else:
        parser.print_help()


def _print_summary(report):
    print(f"\n{'='*60}")
    print(f"  Policy-as-Code Assessment Complete")
    print(f"{'='*60}")
    print(f"  Total policies evaluated:  {report.total_policies}")
    print(f"  Compliant:                {report.compliant} ({report.compliance_rate_pct}%)")
    print(f"  Non-Compliant:            {report.non_compliant}")
    print(f"  Errors:                   {report.errors}")
    print(f"  RAG Status:               {report.rag_status()}")
    crit = report.critical_failures()
    if crit:
        print(f"\n  CRITICAL FAILURES ({len(crit)}):")
        for c in crit:
            print(f"    - {c.policy_id}: {c.finding}")
    print(f"{'='*60}")


def _demo_data() -> list[dict]:
    """Built-in demo data that exercises pass and fail cases."""
    return [
        {
            "_policy_id": "IAM-001",
            "PolicyName": "S3ReadOnly",
            "Action": ["s3:GetObject", "s3:ListBucket"],
            "Resource": ["arn:aws:s3:::my-bucket/*"],
        },
        {
            "_policy_id": "IAM-001",
            "PolicyName": "BadWildcardPolicy",
            "Action": ["*"],
            "Resource": ["*"],
        },
        {
            "_policy_id": "IAM-002",
            "PrincipalName": "alice-dev",
            "AttachedPolicies": [{"PolicyName": "ReadOnlyAccess"}],
        },
        {
            "_policy_id": "IAM-002",
            "PrincipalName": "bob-admin",
            "AttachedPolicies": [{"PolicyName": "AdministratorAccess"}],
        },
        {"_policy_id": "IAM-003", "UserName": "alice-dev", "MFAEnabled": True},
        {"_policy_id": "IAM-003", "UserName": "bob-admin", "MFAEnabled": False},
        {"_policy_id": "IAM-004", "UserName": "alice-dev", "AccessKeyId": "AKIA1234", "KeyAgeDays": 45},
        {"_policy_id": "IAM-004", "UserName": "bob-admin", "AccessKeyId": "AKIA5678", "KeyAgeDays": 120},
        {"_policy_id": "ENC-001", "BucketName": "secure-bucket", "DefaultEncryption": {"Enabled": True, "Algorithm": "AES256"}},
        {"_policy_id": "ENC-001", "BucketName": "insecure-bucket", "DefaultEncryption": {"Enabled": False}},
        {"_policy_id": "ENC-002", "VolumeId": "vol-aaa111", "AvailabilityZone": "eu-west-1a", "Encrypted": True, "KmsKeyId": "arn:aws:kms:..."},
        {"_policy_id": "ENC-002", "VolumeId": "vol-bbb222", "AvailabilityZone": "eu-west-1b", "Encrypted": False, "KmsKeyId": ""},
        {"_policy_id": "ENC-003", "DBInstanceIdentifier": "secure-db", "StorageEncrypted": True, "KmsKeyId": "arn:aws:kms:..."},
        {"_policy_id": "ENC-003", "DBInstanceIdentifier": "insecure-db", "StorageEncrypted": False, "KmsKeyId": ""},
        {"_policy_id": "LOG-001", "TrailName": "main-trail", "IsMultiRegionTrail": True, "IncludeGlobalServiceEvents": True},
        {"_policy_id": "LOG-001", "TrailName": "old-trail", "IsMultiRegionTrail": False, "IncludeGlobalServiceEvents": False},
        {"_policy_id": "LOG-002", "TrailName": "main-trail", "LogFileValidationEnabled": True},
        {"_policy_id": "LOG-002", "TrailName": "old-trail", "LogFileValidationEnabled": False},
        {"_policy_id": "LOG-003", "VpcId": "vpc-secure", "FlowLogsEnabled": True, "FlowLogsDestination": "CloudWatch"},
        {"_policy_id": "LOG-003", "VpcId": "vpc-insecure", "FlowLogsEnabled": False, "FlowLogsDestination": ""},
        {
            "_policy_id": "NET-001", "GroupId": "sg-secure",
            "SecurityGroupRules": [{"Protocol": "tcp", "FromPort": 22, "ToPort": 22, "CidrIp": "10.0.0.0/8"}],
        },
        {
            "_policy_id": "NET-001", "GroupId": "sg-insecure",
            "SecurityGroupRules": [{"Protocol": "tcp", "FromPort": 22, "ToPort": 22, "CidrIp": "0.0.0.0/0"}],
        },
        {
            "_policy_id": "NET-002", "GroupId": "sg-secure",
            "SecurityGroupRules": [{"Protocol": "tcp", "FromPort": 3389, "ToPort": 3389, "CidrIp": "10.0.0.0/8"}],
        },
        {
            "_policy_id": "NET-002", "GroupId": "sg-insecure-rdp",
            "SecurityGroupRules": [{"Protocol": "tcp", "FromPort": 3389, "ToPort": 3389, "CidrIp": "0.0.0.0/0"}],
        },
    ]


if __name__ == "__main__":
    main()

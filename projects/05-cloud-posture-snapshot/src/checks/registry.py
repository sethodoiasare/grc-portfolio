"""CIS benchmark check registry with Vodafone CYBER_038 control mappings.

Maps CIS section numbers to Vodafone control framework D-statements.
"""

# CIS section → Vodafone control mapping per the cloud-cis-posture-snapshot skill
CIS_TO_VODAFONE = {
    "1": ("Management of privileged access rights", "D1-D5"),
    "2": ("Security event logging & monitoring", "D1-D7"),
    "3": ("Firewall rule base management / Segregation", "D1-D10"),
    "4": ("Management of technical vulnerabilities", "D1-D6"),
    "5": ("Compliance with hardening standards (CYBER_038)", "D1-D3"),
    "6": ("Information access restriction", "D1-D6"),
    "7": ("Protection of information in transit", "D1-D17"),
    "8": ("Network intrusion detection", "D1-D10"),
    "9": ("Information backup", "D1-D2"),
    "10": ("Secure system management & protection", "D1-D3"),
}


def get_vodafone_mapping(cis_section: str) -> tuple[str, str]:
    """Return (control_name, d_statement) for a CIS section number."""
    section_key = cis_section.split(".")[0]
    return CIS_TO_VODAFONE.get(section_key, ("General security control", "D1"))


# CIS benchmark versions per provider
BENCHMARK_VERSIONS = {
    "AWS": "CIS AWS Foundations v1.5",
    "AZURE": "CIS Microsoft Azure Foundations v2.0",
    "GCP": "CIS Google Cloud Platform Foundation v2.0",
}


# Check registry — defines every check implemented per provider
AWS_CHECKS: list[dict] = [
    # IAM (1.x)
    {"id": "1.1", "title": "Avoid use of root account", "section": "1", "severity": "CRITICAL"},
    {"id": "1.2", "title": "MFA enabled for root account", "section": "1", "severity": "CRITICAL"},
    {"id": "1.4", "title": "IAM access key rotation (max 90 days)", "section": "1", "severity": "HIGH"},
    {"id": "1.5", "title": "IAM password policy — minimum length >= 14", "section": "1", "severity": "MEDIUM"},
    {"id": "1.7", "title": "MFA enabled for console users", "section": "1", "severity": "HIGH"},
    {"id": "1.14", "title": "No root access key exists", "section": "1", "severity": "CRITICAL"},
    {"id": "1.16", "title": "No full admin policies attached to IAM principals", "section": "1", "severity": "HIGH"},
    # Logging (2.x)
    {"id": "2.1", "title": "CloudTrail enabled in all regions", "section": "2", "severity": "HIGH"},
    {"id": "2.2", "title": "CloudTrail log file validation enabled", "section": "2", "severity": "MEDIUM"},
    {"id": "2.3", "title": "S3 bucket for CloudTrail not publicly accessible", "section": "2", "severity": "HIGH"},
    {"id": "2.4", "title": "CloudTrail integrated with CloudWatch Logs", "section": "2", "severity": "MEDIUM"},
    {"id": "2.7", "title": "VPC flow logging enabled in all VPCs", "section": "2", "severity": "MEDIUM"},
    # Monitoring (3.x)
    {"id": "3.1", "title": "CloudWatch alarm for root account usage", "section": "3", "severity": "MEDIUM"},
    {"id": "3.3", "title": "CloudWatch alarm for unauthorized API calls", "section": "3", "severity": "MEDIUM"},
    {"id": "3.7", "title": "CloudWatch alarm for MFA console sign-in events", "section": "3", "severity": "LOW"},
    # Networking (5.x)
    {"id": "5.1", "title": "No unrestricted ingress to port 22 (SSH)", "section": "5", "severity": "HIGH"},
    {"id": "5.2", "title": "Default security groups block all traffic", "section": "5", "severity": "HIGH"},
    {"id": "5.3", "title": "No unrestricted ingress to port 3389 (RDP)", "section": "5", "severity": "HIGH"},
    # Storage (S3)
    {"id": "S3.1", "title": "S3 bucket versioning enabled", "section": "6", "severity": "LOW"},
    {"id": "S3.2", "title": "S3 bucket MFA delete enabled", "section": "6", "severity": "MEDIUM"},
    {"id": "S3.3", "title": "S3 Block Public Access enabled at account level", "section": "6", "severity": "CRITICAL"},
    # Encryption
    {"id": "EBS.1", "title": "EBS encryption enabled by default", "section": "7", "severity": "MEDIUM"},
]

AZURE_CHECKS: list[dict] = [
    # Identity (1.x)
    {"id": "1.1", "title": "MFA for all users with owner role", "section": "1", "severity": "CRITICAL"},
    {"id": "1.2", "title": "MFA for all users in subscription", "section": "1", "severity": "HIGH"},
    {"id": "1.5", "title": "Guest users reviewed within 30 days", "section": "1", "severity": "MEDIUM"},
    {"id": "1.9", "title": "MFA enabled for all Azure AD users", "section": "1", "severity": "HIGH"},
    # Security Center (2.x)
    {"id": "2.1", "title": "Defender for Cloud — Servers plan enabled", "section": "4", "severity": "HIGH"},
    {"id": "2.2", "title": "Defender for Cloud — SQL plan enabled", "section": "4", "severity": "MEDIUM"},
    {"id": "2.3", "title": "Defender for Cloud — Storage plan enabled", "section": "4", "severity": "MEDIUM"},
    # Storage (3.x)
    {"id": "3.1", "title": "Storage accounts require secure transfer (HTTPS)", "section": "6", "severity": "HIGH"},
    {"id": "3.7", "title": "Storage accounts public blob access disabled", "section": "6", "severity": "CRITICAL"},
    # Databases (4.x)
    {"id": "4.1", "title": "SQL server auditing enabled", "section": "2", "severity": "MEDIUM"},
    # Logging (5.x)
    {"id": "5.1", "title": "Activity log alert for policy assignment changes", "section": "2", "severity": "MEDIUM"},
    {"id": "5.3", "title": "Activity log alert for security group changes", "section": "2", "severity": "MEDIUM"},
    # Networking (6.x)
    {"id": "6.1", "title": "RDP not open from internet (NSG rule)", "section": "5", "severity": "HIGH"},
    {"id": "6.2", "title": "SSH not open from internet (NSG rule)", "section": "5", "severity": "HIGH"},
    {"id": "6.5", "title": "Network Watcher enabled in all regions", "section": "8", "severity": "MEDIUM"},
    # Encryption
    {"id": "ENC.1", "title": "Azure Disk Encryption enabled for VMs", "section": "7", "severity": "MEDIUM"},
]

GCP_CHECKS: list[dict] = [
    # IAM (1.x)
    {"id": "1.1", "title": "No service account has admin privileges", "section": "1", "severity": "CRITICAL"},
    {"id": "1.4", "title": "Service account key rotation (max 90 days)", "section": "1", "severity": "HIGH"},
    {"id": "1.6", "title": "No user-managed keys for Google-managed service accounts", "section": "1", "severity": "MEDIUM"},
    {"id": "1.7", "title": "API keys not in use (use service accounts instead)", "section": "1", "severity": "HIGH"},
    # Logging (2.x)
    {"id": "2.1", "title": "Cloud Audit Logs enabled for all services", "section": "2", "severity": "HIGH"},
    {"id": "2.2", "title": "Log sinks configured for all log entries", "section": "2", "severity": "MEDIUM"},
    {"id": "2.3", "title": "Audit logs not exportable by project editors", "section": "2", "severity": "LOW"},
    # Networking (3.x)
    {"id": "3.1", "title": "Default VPC firewall — no open SSH (22)", "section": "3", "severity": "HIGH"},
    {"id": "3.2", "title": "Default VPC firewall — no open RDP (3389)", "section": "3", "severity": "HIGH"},
    {"id": "3.3", "title": "No firewall rules with 0.0.0.0/0 on all ports", "section": "3", "severity": "CRITICAL"},
    {"id": "3.6", "title": "VPC flow logging enabled", "section": "8", "severity": "MEDIUM"},
    # Storage (4.x)
    {"id": "4.1", "title": "Cloud Storage buckets not publicly accessible", "section": "6", "severity": "CRITICAL"},
    # Encryption
    {"id": "ENC.1", "title": "Default CMEK configured for Cloud Storage", "section": "7", "severity": "MEDIUM"},
    {"id": "ENC.2", "title": "Default CMEK configured for Compute Engine disks", "section": "7", "severity": "MEDIUM"},
]

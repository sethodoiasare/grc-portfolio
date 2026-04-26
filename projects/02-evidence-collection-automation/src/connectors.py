"""
Connector Engine with Simulated and Live System Integrations.

Each connector has two modes:
  - 'simulated': generates realistic sample data marked [SIMULATED]
  - 'live': connects to real Vodafone systems via their native APIs

Mode is stored in the connectors table and dispatched in ConnectorBase.run().
Real integration logic lives in src/integration.py.

All generated data is marked [SIMULATED] for audit transparency.
"""

import random
import uuid
import os
from datetime import datetime, timedelta
from typing import Optional
from src.models import EvidenceItem


def _sim_date(days_ago: int = 0) -> str:
    return (datetime.utcnow() - timedelta(days=days_ago)).isoformat() + "Z"


def _sim_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"


# ---------------------------------------------------------------------------
# Connector Base
# ---------------------------------------------------------------------------


class ConnectorBase:
    name: str = "base"
    connector_type: str = "base"

    def run(self, config: dict | None = None, market_name: str = "Unknown",
            mode: str = "simulated", auth_config: object = None) -> list[EvidenceItem]:
        """Dispatch to simulate() or live collect() based on mode."""
        if mode == "live" and os.environ.get("INTEGRATION_MODE") == "live":
            from src.integration import run_live_collection
            return run_live_collection(self.connector_type, auth_config, market_name)
        return self.simulate(market_name, config or {})

    def simulate(self, market_name: str, config: dict) -> list[EvidenceItem]:
        raise NotImplementedError


# ---------------------------------------------------------------------------
# 1. Active Directory Simulator
# ---------------------------------------------------------------------------


class ADSimulator(ConnectorBase):
    name = "Active Directory"
    connector_type = "sim_ad"

    def simulate(self, market_name: str, config: dict) -> list[EvidenceItem]:
        items: list[EvidenceItem] = []
        now = datetime.utcnow()
        domain = f"VODAFONE\\{market_name.replace(' ', '').upper()[:8]}"

        # --- User List ---
        users = []
        departments = ["IT", "Finance", "HR", "Operations", "Legal", "Marketing", "Cyber Security"]
        for i in range(random.randint(25, 60)):
            dept = random.choice(departments)
            last_logon = now - timedelta(days=random.randint(0, 45))
            users.append({
                "sam_account_name": f"user{i:03d}",
                "display_name": f"{random.choice(['John','Sarah','Mike','Emma','David','Lisa','Alex','Maria'])} {random.choice(['Smith','Jones','Brown','Taylor','Wilson','Davies'])}",
                "department": dept,
                "title": f"{random.choice(['Manager','Analyst','Engineer','Specialist','Lead'])}",
                "enabled": random.random() > 0.05,
                "last_logon_date": last_logon.isoformat(),
                "password_last_set": (now - timedelta(days=random.randint(10, 90))).isoformat(),
                "member_of": random.sample(
                    ["Domain Users", "Domain Admins", f"{dept}_Users", "VPN_Users", "MFA_Required", "Privileged_Access"],
                    k=random.randint(2, 5),
                ),
            })
        items.append(EvidenceItem(
            evidence_type="user_list",
            source_system="Active Directory",
            data={"domain": domain, "user_count": len(users), "users": users},
            freshness_date=_sim_date(0),
            control_mapping=["IAM_001", "IAM_002", "IAM_003", "IAM_004"],
        ))

        # --- MFA Status ---
        mfa_enabled = random.randint(85, 100)
        items.append(EvidenceItem(
            evidence_type="mfa_status",
            source_system="Active Directory",
            data={
                "total_users": len(users),
                "mfa_enabled_pct": mfa_enabled,
                "mfa_disabled_count": len(users) - int(len(users) * mfa_enabled / 100),
                "mfa_methods": {
                    "Microsoft Authenticator": int(len(users) * 0.7),
                    "SMS": int(len(users) * 0.2),
                    "Hardware Token": int(len(users) * 0.1),
                },
                "note": "[SIMULATED] MFA status from simulated AD data",
            },
            freshness_date=_sim_date(0),
            control_mapping=["IAM_005", "IAM_006"],
        ))

        # --- Group Membership Audit ---
        privileged_groups = {
            "Domain Admins": random.randint(2, 8),
            "Enterprise Admins": random.randint(1, 4),
            "Schema Admins": random.randint(1, 3),
            "Privileged_Access": random.randint(5, 15),
        }
        items.append(EvidenceItem(
            evidence_type="group_membership",
            source_system="Active Directory",
            data={
                "privileged_groups": [
                    {"name": g, "member_count": c, "last_reviewed": _sim_date(random.randint(30, 180))}
                    for g, c in privileged_groups.items()
                ],
                "empty_groups": random.randint(2, 8),
                "note": "[SIMULATED] Group membership audit snapshot",
            },
            freshness_date=_sim_date(0),
            control_mapping=["IAM_007", "IAM_008", "IAM_009"],
        ))

        return items


# ---------------------------------------------------------------------------
# 2. MDM / Intune Simulator
# ---------------------------------------------------------------------------


class MDMSimulator(ConnectorBase):
    name = "MDM / Intune"
    connector_type = "sim_mdm"

    def simulate(self, market_name: str, config: dict) -> list[EvidenceItem]:
        items: list[EvidenceItem] = []

        device_types = [
            ("iPhone 15", "iOS 17.4", "smartphone"),
            ("iPhone 14", "iOS 17.3", "smartphone"),
            ("Samsung Galaxy S24", "Android 14", "smartphone"),
            ("iPad Air", "iPadOS 17.4", "tablet"),
            ("iPad Pro", "iPadOS 17.3", "tablet"),
            ("Samsung Galaxy Tab S9", "Android 14", "tablet"),
            ("Surface Pro 9", "Windows 11", "laptop"),
            ("Dell Latitude 7450", "Windows 11", "laptop"),
            ("MacBook Pro M3", "macOS 14", "laptop"),
        ]

        devices = []
        for i in range(random.randint(40, 80)):
            dt = random.choice(device_types)
            devices.append({
                "device_id": _sim_id("DEV"),
                "device_name": f"{market_name[:4]}-{dt[0].replace(' ', '')[:8]}-{i:03d}",
                "device_type": dt[2],
                "make_model": dt[0],
                "os_version": dt[1],
                "enrollment_status": "compliant" if random.random() > 0.08 else "non_compliant",
                "last_check_in": _sim_id("CHK") if random.random() > 0.05 else _sim_date(0),
                "encryption_enabled": random.random() > 0.03,
                "jailbroken_rooted": random.random() < 0.02,
            })

        items.append(EvidenceItem(
            evidence_type="device_compliance",
            source_system="MDM / Intune",
            data={
                "total_devices": len(devices),
                "compliant": sum(1 for d in devices if d["enrollment_status"] == "compliant"),
                "non_compliant": sum(1 for d in devices if d["enrollment_status"] != "compliant"),
                "encryption_rate_pct": round(sum(1 for d in devices if d["encryption_enabled"]) / len(devices) * 100, 1),
                "devices": devices,
                "note": "[SIMULATED] MDM device compliance snapshot",
            },
            freshness_date=_sim_date(0),
            control_mapping=["ENDPOINT_001", "ENDPOINT_002", "ENDPOINT_006"],
        ))

        items.append(EvidenceItem(
            evidence_type="device_enrollment",
            source_system="MDM / Intune",
            data={
                "enrollment_methods": {
                    "Apple Automated Device Enrollment": random.randint(20, 40),
                    "Android Enterprise": random.randint(15, 30),
                    "Windows Autopilot": random.randint(5, 15),
                    "Manual Enrollment": random.randint(0, 5),
                },
                "pending_enrollments": random.randint(0, 4),
                "note": "[SIMULATED] Device enrollment summary",
            },
            freshness_date=_sim_date(0),
            control_mapping=["ENDPOINT_001"],
        ))

        items.append(EvidenceItem(
            evidence_type="os_version",
            source_system="MDM / Intune",
            data={
                "ios_versions": {"17.4": random.randint(20, 40), "17.3": random.randint(5, 15), "16.x": random.randint(2, 8)},
                "android_versions": {"14": random.randint(15, 30), "13": random.randint(3, 10)},
                "windows_versions": {"11": random.randint(5, 15)},
                "outdated_count": random.randint(3, 12),
                "note": "[SIMULATED] OS version distribution",
            },
            freshness_date=_sim_date(0),
            control_mapping=["ENDPOINT_001", "ENDPOINT_005"],
        ))

        return items


# ---------------------------------------------------------------------------
# 3. Firewall Config Simulator
# ---------------------------------------------------------------------------


class FirewallSimulator(ConnectorBase):
    name = "Firewall Config"
    connector_type = "sim_firewall"

    def simulate(self, market_name: str, config: dict) -> list[EvidenceItem]:
        items: list[EvidenceItem] = []
        vendors = ["Palo Alto", "Cisco ASA", "Fortinet", "Check Point"]
        vendor = random.choice(vendors)

        rules = []
        services = ["HTTPS", "SSH", "RDP", "DNS", "NTP", "SMTP", "LDAP", "SMB", "SQL", "Custom App"]
        for i in range(random.randint(30, 80)):
            rules.append({
                "rule_id": i + 1,
                "name": f"Rule-{i + 1:03d}",
                "source": random.choice(["10.0.0.0/8", "172.16.0.0/12", "192.168.1.0/24", "ANY", "VPN_Pool"]),
                "destination": random.choice(["DMZ", "Internal", "Internet", "VPN_Endpoint", "Specific_IP"]),
                "service": random.choice(services),
                "action": "allow" if random.random() > 0.3 else "deny",
                "log_enabled": random.random() > 0.4,
                "last_modified": _sim_date(random.randint(0, 365)),
                "rule_comment": "Business justification: Required for operations" if random.random() > 0.5 else "",
            })

        items.append(EvidenceItem(
            evidence_type="firewall_rules",
            source_system="Firewall Config",
            data={
                "vendor": vendor,
                "total_rules": len(rules),
                "allow_rules": sum(1 for r in rules if r["action"] == "allow"),
                "deny_rules": sum(1 for r in rules if r["action"] == "deny"),
                "rules_without_comments": sum(1 for r in rules if not r["rule_comment"]),
                "rules_with_logging": sum(1 for r in rules if r["log_enabled"]),
                "rules": rules,
                "note": "[SIMULATED] Firewall rule set analysis",
            },
            freshness_date=_sim_date(0),
            control_mapping=["NETWORK_001", "NETWORK_002", "NETWORK_003"],
        ))

        items.append(EvidenceItem(
            evidence_type="vpn_config",
            source_system="Firewall Config",
            data={
                "vpn_type": random.choice(["IPSec", "SSL VPN", "WireGuard"]),
                "concurrent_sessions_max": random.randint(100, 500),
                "mfa_required": True,
                "split_tunneling": random.choice([True, False]),
                "encryption_algorithm": random.choice(["AES-256-GCM", "AES-256-CBC"]),
                "note": "[SIMULATED] VPN configuration summary",
            },
            freshness_date=_sim_date(0),
            control_mapping=["NETWORK_001", "NETWORK_002"],
        ))

        items.append(EvidenceItem(
            evidence_type="open_ports",
            source_system="Firewall Config",
            data={
                "external_ports": random.sample([22, 80, 443, 3389, 8080, 8443], k=random.randint(2, 5)),
                "internal_ports": random.sample([22, 53, 80, 443, 389, 636, 1433, 3306, 5432, 8080], k=random.randint(4, 8)),
                "port_scan_date": _sim_date(0),
                "note": "[SIMULATED] Open port scan results",
            },
            freshness_date=_sim_date(0),
            control_mapping=["NETWORK_004", "NETWORK_005"],
        ))

        return items


# ---------------------------------------------------------------------------
# 4. Vulnerability Scanner Simulator
# ---------------------------------------------------------------------------


class VulnScannerSimulator(ConnectorBase):
    name = "Vulnerability Scanner"
    connector_type = "sim_vuln"

    def simulate(self, market_name: str, config: dict) -> list[EvidenceItem]:
        scanner = random.choice(["Tenable.io", "Qualys", "Rapid7", "OpenVAS"])

        vulns = []
        vuln_templates = [
            ("CVE-2024-{}", "Remote Code Execution in {}", "CRITICAL", 9.8),
            ("CVE-2024-{}", "Privilege Escalation in {}", "HIGH", 7.5),
            ("CVE-2024-{}", "Information Disclosure in {}", "MEDIUM", 5.3),
            ("CVE-2024-{}", "Denial of Service in {}", "MEDIUM", 4.8),
            ("CVE-2024-{}", "Cross-Site Scripting in {}", "LOW", 3.1),
        ]
        assets = [
            "Windows Server 2019", "Windows Server 2022", "Ubuntu 22.04 LTS",
            "Red Hat Enterprise Linux 9", "Apache HTTP Server 2.4", "nginx 1.24",
            "Microsoft SQL Server 2022", "PostgreSQL 16", "Cisco IOS XE",
            "VMware ESXi 8.0", "Kubernetes 1.29",
        ]

        for i in range(random.randint(15, 40)):
            template = random.choice(vuln_templates)
            asset = random.choice(assets)
            cvss = template[3] + random.uniform(-0.5, 3.5)
            cvss = max(0.1, min(10.0, round(cvss, 1)))

            vulns.append({
                "cve_id": template[0].format(random.randint(1000, 99999)),
                "title": template[1].format(asset),
                "severity": template[2],
                "cvss_score": cvss,
                "affected_asset": asset,
                "discovered_date": _sim_date(random.randint(0, 90)),
                "patch_available": random.random() > 0.2,
                "remediation": "Apply vendor patch" if random.random() > 0.5 else "Configuration change required",
            })

        critical = sum(1 for v in vulns if v["severity"] == "CRITICAL")
        high = sum(1 for v in vulns if v["severity"] == "HIGH")
        patched = sum(1 for v in vulns if v["patch_available"])

        items: list[EvidenceItem] = []
        items.append(EvidenceItem(
            evidence_type="vulnerability_list",
            source_system="Vulnerability Scanner",
            data={
                "scanner": scanner,
                "scan_date": _sim_date(0),
                "total_vulnerabilities": len(vulns),
                "critical": critical,
                "high": high,
                "medium": sum(1 for v in vulns if v["severity"] == "MEDIUM"),
                "low": sum(1 for v in vulns if v["severity"] == "LOW"),
                "patchable_pct": round(patched / len(vulns) * 100, 1),
                "vulnerabilities": vulns,
                "note": "[SIMULATED] Vulnerability scan results",
            },
            freshness_date=_sim_date(0),
            control_mapping=["VULN_MGMT_001"],
        ))

        items.append(EvidenceItem(
            evidence_type="patch_status",
            source_system="Vulnerability Scanner",
            data={
                "systems_patched": random.randint(80, 98),
                "systems_pending": random.randint(2, 15),
                "systems_critical_missing": random.randint(0, 5),
                "patch_compliance_pct": round(random.uniform(85, 99), 1),
                "avg_days_to_patch": round(random.uniform(3, 30), 1),
                "sla_breaches": random.randint(0, 8),
                "note": "[SIMULATED] Patch compliance summary",
            },
            freshness_date=_sim_date(0),
            control_mapping=["VULN_MGMT_001"],
        ))

        return items


# ---------------------------------------------------------------------------
# 5. SIEM Log Extractor Simulator
# ---------------------------------------------------------------------------


class SIEMSimulator(ConnectorBase):
    name = "SIEM Log Extractor"
    connector_type = "sim_siem"

    def simulate(self, market_name: str, config: dict) -> list[EvidenceItem]:
        items: list[EvidenceItem] = []
        siem = random.choice(["Microsoft Sentinel", "Splunk", "QRadar", "Elastic Security"])

        alert_types = [
            ("Brute Force Attempt", "HIGH", "Multiple failed login attempts detected"),
            ("Malware Detection", "CRITICAL", "Endpoint protection triggered"),
            ("Data Exfiltration", "CRITICAL", "Unusual outbound data transfer"),
            ("Privilege Escalation", "HIGH", "Unauthorised admin action detected"),
            ("Suspicious Login", "MEDIUM", "Login from unusual location"),
            ("Policy Violation", "MEDIUM", "Traffic to blocked destination"),
            ("Dormant Account Activity", "LOW", "Previously inactive account used"),
        ]

        alerts = []
        for _ in range(random.randint(20, 60)):
            at = random.choice(alert_types)
            alerts.append({
                "alert_id": _sim_id("ALT"),
                "type": at[0],
                "severity": at[1],
                "description": at[2],
                "timestamp": _sim_date(random.randint(0, 30)),
                "status": random.choice(["open", "investigating", "closed"]),
                "assigned_to": random.choice(["SOC-L1", "SOC-L2", "SOC-L3"]) if random.random() > 0.3 else "Unassigned",
            })

        items.append(EvidenceItem(
            evidence_type="alert_volume",
            source_system="SIEM Log Extractor",
            data={
                "siem_platform": siem,
                "period": "Last 30 days",
                "total_alerts": len(alerts),
                "by_severity": {
                    "CRITICAL": sum(1 for a in alerts if a["severity"] == "CRITICAL"),
                    "HIGH": sum(1 for a in alerts if a["severity"] == "HIGH"),
                    "MEDIUM": sum(1 for a in alerts if a["severity"] == "MEDIUM"),
                    "LOW": sum(1 for a in alerts if a["severity"] == "LOW"),
                },
                "open_alerts": sum(1 for a in alerts if a["status"] == "open"),
                "unassigned_alerts": sum(1 for a in alerts if a["assigned_to"] == "Unassigned"),
                "alerts": alerts,
                "note": "[SIMULATED] SIEM alert summary",
            },
            freshness_date=_sim_date(0),
            control_mapping=["SIEM_001", "SIEM_002"],
        ))

        items.append(EvidenceItem(
            evidence_type="log_sources",
            source_system="SIEM Log Extractor",
            data={
                "total_sources": random.randint(30, 80),
                "sources_by_type": {
                    "Windows Event Logs": random.randint(10, 30),
                    "Linux Syslog": random.randint(5, 15),
                    "Network Devices": random.randint(5, 15),
                    "Firewall": random.randint(2, 6),
                    "IDS/IPS": random.randint(1, 4),
                    "Cloud (Azure/AWS)": random.randint(3, 8),
                },
                "sources_not_reporting": random.randint(0, 5),
                "log_retention_days": random.choice([90, 180, 365]),
                "note": "[SIMULATED] Log source inventory",
            },
            freshness_date=_sim_date(0),
            control_mapping=["SIEM_001"],
        ))

        items.append(EvidenceItem(
            evidence_type="correlation_rules",
            source_system="SIEM Log Extractor",
            data={
                "total_rules": random.randint(25, 60),
                "enabled_rules": random.randint(20, 55),
                "disabled_rules": random.randint(2, 8),
                "last_tuned": _sim_date(random.randint(30, 180)),
                "false_positive_rate_pct": round(random.uniform(5, 25), 1),
                "note": "[SIMULATED] Correlation rule health check",
            },
            freshness_date=_sim_date(0),
            control_mapping=["SIEM_002"],
        ))

        return items


# ---------------------------------------------------------------------------
# 6. Endpoint DLP Simulator
# ---------------------------------------------------------------------------


class DLPSimulator(ConnectorBase):
    name = "Endpoint DLP"
    connector_type = "sim_dlp"

    def simulate(self, market_name: str, config: dict) -> list[EvidenceItem]:
        items: list[EvidenceItem] = []
        dlp = random.choice(["Microsoft Purview", "Symantec DLP", "Forcepoint DLP"])

        events = []
        event_types = [
            ("USB write", "BLOCKED", "Confidential document copied to removable media"),
            ("Email attachment", "BLOCKED", "PII detected in outbound email attachment"),
            ("Print", "ALLOWED", "Document printed with classification label"),
            ("Cloud upload", "BLOCKED", "Sensitive file upload to personal cloud storage"),
            ("Screen capture", "AUDITED", "Screen capture attempted on classified document"),
        ]

        for _ in range(random.randint(15, 40)):
            et = random.choice(event_types)
            events.append({
                "event_id": _sim_id("DLP"),
                "type": et[0],
                "action": et[1],
                "description": et[2],
                "timestamp": _sim_date(random.randint(0, 14)),
                "user": f"user{random.randint(1, 60):03d}@vodafone.com",
                "endpoint": f"LAPTOP-{random.randint(100, 999):03d}",
                "classification": random.choice(["Confidential", "Internal", "Public", "Restricted"]),
            })

        items.append(EvidenceItem(
            evidence_type="dlp_events",
            source_system="Endpoint DLP",
            data={
                "dlp_platform": dlp,
                "period": "Last 14 days",
                "total_events": len(events),
                "blocked": sum(1 for e in events if e["action"] == "BLOCKED"),
                "allowed": sum(1 for e in events if e["action"] == "ALLOWED"),
                "audited": sum(1 for e in events if e["action"] == "AUDITED"),
                "events": events,
                "note": "[SIMULATED] DLP event log extract",
            },
            freshness_date=_sim_date(0),
            control_mapping=["DATA_001", "DATA_002"],
        ))

        items.append(EvidenceItem(
            evidence_type="dlp_channels",
            source_system="Endpoint DLP",
            data={
                "monitored_channels": [
                    {"name": "USB Ports", "status": "protected"},
                    {"name": "Email (SMTP)", "status": "protected"},
                    {"name": "Web (HTTP/HTTPS)", "status": "protected"},
                    {"name": "Print", "status": "monitored"},
                    {"name": "Bluetooth", "status": "blocked"},
                    {"name": "CD/DVD Burner", "status": "blocked"},
                    {"name": "Cloud Storage", "status": "protected"},
                ],
                "endpoint_coverage_pct": random.randint(85, 100),
                "note": "[SIMULATED] DLP channel configuration",
            },
            freshness_date=_sim_date(0),
            control_mapping=["DATA_003", "DATA_004"],
        ))

        items.append(EvidenceItem(
            evidence_type="dlp_ruleset",
            source_system="Endpoint DLP",
            data={
                "ruleset_version": f"{random.randint(2,5)}.{random.randint(0,9)}.{random.randint(0,99)}",
                "last_updated": _sim_date(random.randint(0, 30)),
                "total_rules": random.randint(30, 80),
                "categories": ["PII", "PCI", "PHI", "IP", "Source Code", "Financial Data"],
                "note": "[SIMULATED] DLP ruleset configuration",
            },
            freshness_date=_sim_date(0),
            control_mapping=["DATA_003"],
        ))

        return items


# ---------------------------------------------------------------------------
# 7. Manual Upload Connector
# ---------------------------------------------------------------------------


class ManualUploadConnector(ConnectorBase):
    name = "Manual Upload"
    connector_type = "manual"

    def simulate(self, market_name: str, config: dict) -> list[EvidenceItem]:
        return [EvidenceItem(
            evidence_type="manual_evidence",
            source_system="Manual Upload",
            data={
                "description": config.get("description", "Manually uploaded evidence"),
                "file_count": config.get("file_count", 1),
                "market": market_name,
                "note": "[SIMULATED] Manual evidence upload. Replace with real files in production.",
            },
            freshness_date=_sim_date(0),
            control_mapping=config.get("control_ids", []),
        )]


# ---------------------------------------------------------------------------
# Connector Registry
# ---------------------------------------------------------------------------


CONNECTORS: dict[str, ConnectorBase] = {
    "sim_ad": ADSimulator(),
    "sim_mdm": MDMSimulator(),
    "sim_firewall": FirewallSimulator(),
    "sim_vuln": VulnScannerSimulator(),
    "sim_siem": SIEMSimulator(),
    "sim_dlp": DLPSimulator(),
    "manual": ManualUploadConnector(),
}


def get_connector(connector_type: str) -> ConnectorBase | None:
    return CONNECTORS.get(connector_type)

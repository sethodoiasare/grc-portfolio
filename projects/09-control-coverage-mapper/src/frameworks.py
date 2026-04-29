"""Built-in security control framework catalogs for coverage mapping."""

from .models import ControlStatement, CoverageStatus


def _control(framework: str, control_id: str, title: str, description: str, category: str) -> ControlStatement:
    return ControlStatement(
        framework=framework,
        control_id=control_id,
        title=title,
        description=description,
        category=category,
        status=CoverageStatus.GAP,
    )


def iso27001_2022() -> list[ControlStatement]:
    """ISO/IEC 27001:2022 Annex A controls — 15 key controls."""
    return [
        _control("ISO27001", "A.5.1", "Policies for Information Security",
                 "A set of policies for information security shall be defined, approved by management, published and communicated.",
                 "Governance"),
        _control("ISO27001", "A.5.4", "Management Responsibilities",
                 "Management shall require all personnel to apply information security in accordance with the established ISMS.",
                 "Governance"),
        _control("ISO27001", "A.5.7", "Threat Intelligence",
                 "Information relating to information security threats shall be collected and analysed to produce threat intelligence.",
                 "Governance"),
        _control("ISO27001", "A.5.15", "Access Control",
                 "Rules to control physical and logical access to information and other associated assets shall be established.",
                 "Access Control"),
        _control("ISO27001", "A.5.17", "Authentication Information",
                 "Allocation and management of authentication information shall be controlled by a formal management process.",
                 "Access Control"),
        _control("ISO27001", "A.5.18", "Access Rights",
                 "Access rights shall be reviewed, removed or adjusted as changes occur, such as personnel leaving the organisation.",
                 "Access Control"),
        _control("ISO27001", "A.6.1", "Screening",
                 "Background verification checks on all candidates for employment shall be carried out in accordance with relevant laws.",
                 "HR Security"),
        _control("ISO27001", "A.6.6", "Confidentiality Agreements",
                 "Confidentiality or non-disclosure agreements reflecting the organisation's needs shall be identified, documented and reviewed.",
                 "HR Security"),
        _control("ISO27001", "A.7.9", "Security of Assets Off-Premises",
                 "Devices and assets used outside the organisation's premises shall be protected.",
                 "Asset Management"),
        _control("ISO27001", "A.8.1", "User Endpoint Devices",
                 "Information stored on, processed by or accessible via user endpoint devices shall be protected.",
                 "Endpoint Security"),
        _control("ISO27001", "A.8.8", "Vulnerability Management",
                 "Information about technical vulnerabilities of information systems in use shall be obtained and evaluated.",
                 "Vulnerability Management"),
        _control("ISO27001", "A.8.12", "Data Leakage Prevention",
                 "Measures shall be applied to prevent the unauthorised disclosure of information from systems, networks and devices.",
                 "Data Protection"),
        _control("ISO27001", "A.8.15", "Logging",
                 "Logs that record activities, exceptions, faults and other relevant events shall be produced, kept and regularly reviewed.",
                 "Monitoring"),
        _control("ISO27001", "A.8.16", "Monitoring Activities",
                 "Networks, systems and applications shall be monitored for anomalous behaviour and evaluated.",
                 "Monitoring"),
        _control("ISO27001", "A.8.25", "Secure Development Lifecycle",
                 "Rules for the secure development of software and systems shall be established and applied.",
                 "Development"),
    ]


def nist_csf() -> list[ControlStatement]:
    """NIST Cybersecurity Framework — 15 key subcategories across the five functions."""
    return [
        _control("NIST_CSF", "ID.AM-2", "Software and Applications Inventory",
                 "Software platforms and applications within the organisation are inventoried.",
                 "Identify — Asset Management"),
        _control("NIST_CSF", "ID.RA-1", "Asset Vulnerabilities",
                 "Asset vulnerabilities are identified and documented.",
                 "Identify — Risk Assessment"),
        _control("NIST_CSF", "ID.GV-1", "Organisational Cybersecurity Policy",
                 "Organisational cybersecurity policy is established and communicated.",
                 "Identify — Governance"),
        _control("NIST_CSF", "ID.RM-1", "Risk Management Processes",
                 "Risk management processes are established, managed and agreed to by organisational stakeholders.",
                 "Identify — Risk Management"),
        _control("NIST_CSF", "PR.AA-1", "Identity and Credential Management",
                 "Identities and credentials for authorised users and services are managed.",
                 "Protect — Access Control"),
        _control("NIST_CSF", "PR.AA-2", "Physical Access Control",
                 "Physical access to assets is managed and protected.",
                 "Protect — Access Control"),
        _control("NIST_CSF", "PR.DS-1", "Data-at-Rest Protection",
                 "Data at rest is protected.",
                 "Protect — Data Security"),
        _control("NIST_CSF", "PR.DS-2", "Data-in-Transit Protection",
                 "Data in transit is protected.",
                 "Protect — Data Security"),
        _control("NIST_CSF", "PR.MA-1", "Maintenance and Repair",
                 "Assets are maintained and repairs are performed and logged with approved and controlled tools.",
                 "Protect — Maintenance"),
        _control("NIST_CSF", "DE.CM-1", "Network Monitoring",
                 "Networks and network services are monitored for anomalous behaviour.",
                 "Detect — Continuous Monitoring"),
        _control("NIST_CSF", "DE.CM-7", "Personnel Activity Monitoring",
                 "Personnel activity is monitored to detect potential cybersecurity events.",
                 "Detect — Continuous Monitoring"),
        _control("NIST_CSF", "DE.AE-2", "Event Analysis",
                 "Analysed events are analysed to understand attack targets and methods.",
                 "Detect — Anomalies and Events"),
        _control("NIST_CSF", "RS.MA-1", "Incident Response Plan Execution",
                 "Incident response plan is executed during or after an incident.",
                 "Respond — Analysis"),
        _control("NIST_CSF", "RS.CO-3", "Vulnerability Disclosure",
                 "Vulnerability information is shared with designated parties.",
                 "Respond — Communications"),
        _control("NIST_CSF", "RC.RP-1", "Recovery Plan Execution",
                 "Recovery plan is executed during or after a cybersecurity incident.",
                 "Recover — Recovery Planning"),
    ]


def cis_v8() -> list[ControlStatement]:
    """CIS Critical Security Controls v8 — 10 key safeguards."""
    return [
        _control("CIS_V8", "CIS 1.1", "Enterprise Asset Inventory",
                 "Establish and maintain an accurate, detailed, and up-to-date inventory of all enterprise assets.",
                 "Inventory and Control of Enterprise Assets"),
        _control("CIS_V8", "CIS 2.1", "Software Inventory",
                 "Establish and maintain a detailed inventory of all licensed software installed on enterprise assets.",
                 "Inventory and Control of Software Assets"),
        _control("CIS_V8", "CIS 4.1", "Secure Configuration of Endpoints",
                 "Establish and maintain a secure configuration process for enterprise assets and software.",
                 "Secure Configuration of Assets"),
        _control("CIS_V8", "CIS 5.1", "Account Inventory",
                 "Establish and maintain an inventory of all accounts managed in the enterprise.",
                 "Account Management"),
        _control("CIS_V8", "CIS 5.4", "Use of Privileged Accounts",
                 "Restrict the use of privileged accounts to dedicated users on dedicated systems.",
                 "Account Management"),
        _control("CIS_V8", "CIS 6.3", "Require MFA",
                 "Require multi-factor authentication for all users, without exception.",
                 "Access Control Management"),
        _control("CIS_V8", "CIS 8.1", "Audit Log Collection",
                 "Collect detailed audit logs for all enterprise assets.",
                 "Audit Log Management"),
        _control("CIS_V8", "CIS 10.1", "Anti-Malware Deployment",
                 "Deploy and maintain anti-malware software on all enterprise assets.",
                 "Malware Defences"),
        _control("CIS_V8", "CIS 12.1", "Network Infrastructure",
                 "Ensure network infrastructure is up to date and configured securely.",
                 "Network Infrastructure Management"),
        _control("CIS_V8", "CIS 17.1", "Incident Response Plan",
                 "Establish and maintain an incident response plan.",
                 "Incident Response Management"),
    ]


def vodafone_tier2() -> list[ControlStatement]:
    """Vodafone-aligned Tier 2 controls (D/E statement based) — 15 controls."""
    return [
        _control("VODAFONE", "VOD-ACC-001", "Management of Privileged Access Rights",
                 "D1-D5: Privileged access rights shall be formally requested, approved, provisioned and reviewed on a periodic basis.",
                 "Access Control"),
        _control("VODAFONE", "VOD-ACC-002", "User Access Reviews",
                 "D6-D8: Periodic recertification of user access rights shall be conducted by asset owners.",
                 "Access Control"),
        _control("VODAFONE", "VOD-ENP-001", "Endpoint Protection",
                 "E1-E3: All endpoint devices shall be equipped with anti-malware, host firewall and disk encryption.",
                 "Endpoint Security"),
        _control("VODAFONE", "VOD-ENP-002", "Mobile Device Management",
                 "E4: Mobile devices that access corporate data shall be enrolled in an MDM platform with policy enforcement.",
                 "Endpoint Security"),
        _control("VODAFONE", "VOD-NET-001", "Network Segmentation",
                 "E1-E2: Production and non-production environments shall be segregated by network controls.",
                 "Network Security"),
        _control("VODAFONE", "VOD-NET-002", "Firewall Rule Review",
                 "E3-E4: Firewall rules shall be reviewed at least quarterly to identify and remove unused rules.",
                 "Network Security"),
        _control("VODAFONE", "VOD-CLD-001", "Cloud Security Posture",
                 "E1-E3: Cloud environments shall be configured in accordance with hardening baselines (CIS benchmarks).",
                 "Cloud Security"),
        _control("VODAFONE", "VOD-CLD-002", "Cloud Encryption",
                 "E4: All cloud data stores shall have encryption-at-rest enabled with customer-managed keys where applicable.",
                 "Cloud Security"),
        _control("VODAFONE", "VOD-VUL-001", "Vulnerability Scanning",
                 "E1-E3: Automated vulnerability scanning shall be performed across internal and external assets on a weekly basis.",
                 "Vulnerability Management"),
        _control("VODAFONE", "VOD-VUL-002", "Patch Management",
                 "E4-E6: Security patches shall be applied within SLA: critical/7d, high/14d, medium/30d.",
                 "Vulnerability Management"),
        _control("VODAFONE", "VOD-MON-001", "Security Monitoring",
                 "E1-E2: SIEM shall collect and correlate security events from all critical assets 24/7.",
                 "Security Monitoring"),
        _control("VODAFONE", "VOD-MON-002", "Alert Response",
                 "E3-E4: Security alerts shall be triaged within 30 minutes and investigated by a qualified analyst.",
                 "Security Monitoring"),
        _control("VODAFONE", "VOD-SUP-001", "Supplier Risk Assessment",
                 "E1-E3: All third-party suppliers with access to sensitive data shall undergo a risk assessment prior to engagement.",
                 "Supplier Security"),
        _control("VODAFONE", "VOD-BCP-001", "Business Continuity Testing",
                 "D1-D3: Business continuity and disaster recovery plans shall be tested at least annually.",
                 "Business Continuity"),
        _control("VODAFONE", "VOD-INC-001", "Incident Response",
                 "E1-E4: A formal incident response plan shall be maintained, tested, and reviewed after each significant incident.",
                 "Incident Response"),
    ]


FRAMEWORK_REGISTRY = {
    "ISO27001": iso27001_2022,
    "NIST_CSF": nist_csf,
    "CIS_V8": cis_v8,
    "VODAFONE": vodafone_tier2,
}


def get_framework(name: str) -> list[ControlStatement]:
    """Return a fresh copy of controls for the named framework."""
    fn = FRAMEWORK_REGISTRY.get(name.upper())
    if fn is None:
        raise KeyError(f"Unknown framework '{name}'. Available: {list(FRAMEWORK_REGISTRY.keys())}")
    return fn()


def list_frameworks() -> list[str]:
    """Return list of available framework names."""
    return list(FRAMEWORK_REGISTRY.keys())

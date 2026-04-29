"""Built-in demo risk register with 12+ risks covering all categories and statuses."""

from datetime import date, timedelta

from .models import (
    Risk, RiskRegister, RiskCategory, RiskStatus, RiskLevel,
    SSVCMetric, Exploitation, Automatable, TechnicalImpact, MissionImpact,
    SSVCDecision,
)
from .register import create_risk, add_to_register, accept_risk


def build_demo_register() -> RiskRegister:
    """Build a demo RiskRegister with 12+ diverse risks.

    Returns:
        RiskRegister populated with realistic example risks.
    """
    register = RiskRegister(owner="GRC Team")

    today = date.today()

    # --- 2 CRITICAL risks ---

    r1 = add_to_register(register, create_risk(
        title="Internet-facing RCE in Web Application",
        description=(
            "Remote code execution vulnerability in the customer-facing web portal "
            "allows unauthenticated attackers to execute arbitrary commands on the "
            "underlying host. Affects all versions prior to 3.2.1."
        ),
        category=RiskCategory.APPLICATION,
        cvss_vector="AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
        ssvc_metric=SSVCMetric(
            exploitation=Exploitation.ACTIVE,
            automatable=Automatable.YES,
            technical_impact=TechnicalImpact.TOTAL,
            mission_impact=MissionImpact.HIGH,
        ),
        owner="appsec-team",
        impact_score=95,
        likelihood_score=85,
        identified_date=today - timedelta(days=14),
        treatment_plan="Emergency patch deployment to v3.2.2; WAF rule to block exploitation attempts.",
        control_mapping=["APP-001", "VULN-003", "NET-005"],
    ))

    r2 = add_to_register(register, create_risk(
        title="Unencrypted Customer PII Database",
        description=(
            "Production database containing full customer PII (names, addresses, "
            "payment instruments) has encryption-at-rest disabled. A disk theft or "
            "cloud snapshot exposure would result in a reportable breach under GDPR."
        ),
        category=RiskCategory.DATA,
        cvss_vector="AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N",
        ssvc_metric=SSVCMetric(
            exploitation=Exploitation.POC,
            automatable=Automatable.YES,
            technical_impact=TechnicalImpact.TOTAL,
            mission_impact=MissionImpact.HIGH,
        ),
        owner="dba-team",
        impact_score=90,
        likelihood_score=60,
        identified_date=today - timedelta(days=30),
        treatment_plan="Enable TDE encryption on all PII columns; rotate storage encryption keys.",
        control_mapping=["DATA-001", "ENC-001", "IAM-002"],
    ))

    # --- 3 HIGH risks ---

    r3 = add_to_register(register, create_risk(
        title="Missing MFA on Privileged Admin Accounts",
        description=(
            "Production AWS IAM admin users and break-glass accounts lack multi-factor "
            "authentication. Credential theft via phishing would grant full administrative "
            "access to the production environment."
        ),
        category=RiskCategory.INFRASTRUCTURE,
        cvss_vector="AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
        ssvc_metric=SSVCMetric(
            exploitation=Exploitation.POC,
            automatable=Automatable.NO,
            technical_impact=TechnicalImpact.TOTAL,
            mission_impact=MissionImpact.MEDIUM,
        ),
        owner="iam-team",
        impact_score=85,
        likelihood_score=40,
        identified_date=today - timedelta(days=45),
        treatment_plan="Enforce MFA via AWS IAM policy; deploy hardware security keys for break-glass accounts.",
        control_mapping=["IAM-001", "IAM-002", "IAM-005"],
    ))

    r4 = add_to_register(register, create_risk(
        title="Weak Password Policy Across Corporate AD",
        description=(
            "Active Directory password policy allows 6-character passwords without "
            "complexity requirements. Numerous service accounts have non-expiring "
            "passwords. Increases risk of brute-force and password-spray attacks."
        ),
        category=RiskCategory.INFRASTRUCTURE,
        cvss_vector="AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
        ssvc_metric=SSVCMetric(
            exploitation=Exploitation.POC,
            automatable=Automatable.YES,
            technical_impact=TechnicalImpact.PARTIAL,
            mission_impact=MissionImpact.HIGH,
        ),
        owner="identity-team",
        impact_score=75,
        likelihood_score=55,
        identified_date=today - timedelta(days=60),
        treatment_plan="Roll out 14-character minimum with complexity; force password rotation for service accounts.",
        control_mapping=["IAM-003", "IAM-004"],
    ))

    r5 = add_to_register(register, create_risk(
        title="Orphaned Privileged Accounts Not Disabled",
        description=(
            "30+ privileged domain and SaaS accounts belonging to departed employees "
            "remain active. No automated joiner-mover-leaver process links HR system "
            "to IAM provisioning. Accounts could be used for persistent lateral movement."
        ),
        category=RiskCategory.HUMAN,
        cvss_vector="AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
        ssvc_metric=SSVCMetric(
            exploitation=Exploitation.NONE,
            automatable=Automatable.YES,
            technical_impact=TechnicalImpact.TOTAL,
            mission_impact=MissionImpact.MEDIUM,
        ),
        owner="hr-it-integration",
        impact_score=80,
        likelihood_score=35,
        identified_date=today - timedelta(days=90),
        treatment_plan="Immediate disable of all flagged accounts; implement SCIM provisioning from HR system.",
        control_mapping=["IAM-006", "HR-001"],
    ))

    # --- 4 MEDIUM risks ---

    r6 = add_to_register(register, create_risk(
        title="Unpatched Endpoints — OS Build Behind by 90+ Days",
        description=(
            "Approximately 15% of the corporate endpoint fleet (200+ Windows laptops) "
            "are running OS builds more than 90 days behind the current patch level. "
            "SCCM reporting confirms missing KBs for critical CVEs."
        ),
        category=RiskCategory.INFRASTRUCTURE,
        cvss_vector="AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:L/A:L",
        ssvc_metric=SSVCMetric(
            exploitation=Exploitation.POC,
            automatable=Automatable.NO,
            technical_impact=TechnicalImpact.PARTIAL,
            mission_impact=MissionImpact.MEDIUM,
        ),
        owner="endpoint-team",
        impact_score=50,
        likelihood_score=60,
        identified_date=today - timedelta(days=21),
        treatment_plan="Force SCCM push for missing patches; implement compliance reporting dashboard.",
        control_mapping=["ENDP-001", "VULN-001"],
    ))

    r7 = add_to_register(register, create_risk(
        title="Default SNMP Community Strings on Network Devices",
        description=(
            "12 core switches and 5 routers still use default SNMP v2c community "
            "strings ('public'/'private'). Information disclosure risk including "
            "network topology, ARP tables, and device configurations."
        ),
        category=RiskCategory.INFRASTRUCTURE,
        cvss_vector="AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N",
        ssvc_metric=SSVCMetric(
            exploitation=Exploitation.NONE,
            automatable=Automatable.YES,
            technical_impact=TechnicalImpact.PARTIAL,
            mission_impact=MissionImpact.MEDIUM,
        ),
        owner="network-team",
        impact_score=45,
        likelihood_score=65,
        identified_date=today - timedelta(days=120),
        treatment_plan="Migrate to SNMP v3 with authentication and encryption; disable v1/v2c.",
        control_mapping=["NET-001", "NET-003"],
    ))

    r8 = add_to_register(register, create_risk(
        title="Stale Database Backups — No Restoration Test in 12 Months",
        description=(
            "Production database backups have not been restored or tested in over "
            "12 months. Backup integrity and recovery time objectives (RTO 4 hours) "
            "cannot be assured. Affects the primary customer data platform."
        ),
        category=RiskCategory.DATA,
        cvss_vector="AV:N/AC:H/PR:H/UI:R/S:U/C:N/I:N/A:H",
        ssvc_metric=SSVCMetric(
            exploitation=Exploitation.NONE,
            automatable=Automatable.NO,
            technical_impact=TechnicalImpact.TOTAL,
            mission_impact=MissionImpact.LOW,
        ),
        owner="dba-team",
        impact_score=65,
        likelihood_score=30,
        identified_date=today - timedelta(days=180),
        treatment_plan="Schedule quarterly restore drills; automate restoration testing pipeline.",
        control_mapping=["DATA-002", "BCDR-001"],
    ))

    r9 = add_to_register(register, create_risk(
        title="Missing Audit Logs for Privileged Database Access",
        description=(
            "Database audit logging is not enabled for the finance schema. SELECT, "
            "INSERT, and UPDATE operations by DBAs are not captured in the SIEM. "
            "Regulatory requirement under SOX and PCI DSS."
        ),
        category=RiskCategory.COMPLIANCE,
        cvss_vector="AV:N/AC:L/PR:H/UI:N/S:U/C:H/I:H/A:N",
        ssvc_metric=SSVCMetric(
            exploitation=Exploitation.NONE,
            automatable=Automatable.NO,
            technical_impact=TechnicalImpact.PARTIAL,
            mission_impact=MissionImpact.MEDIUM,
        ),
        owner="compliance-team",
        impact_score=55,
        likelihood_score=40,
        identified_date=today - timedelta(days=45),
        treatment_plan="Enable fine-grained audit logging on finance schema; ship logs to SIEM.",
        control_mapping=["LOG-001", "LOG-002", "COMP-003"],
    ))

    # --- 2 LOW risks ---

    r10 = add_to_register(register, create_risk(
        title="Self-Signed Certificates on Internal Tools",
        description=(
            "Several internal admin consoles (Jenkins, Grafana, internal wiki) use "
            "self-signed TLS certificates. While not externally accessible, this "
            "normalises certificate warning bypass behaviour among administrators."
        ),
        category=RiskCategory.INFRASTRUCTURE,
        cvss_vector="AV:A/AC:H/PR:N/UI:R/S:U/C:L/I:N/A:N",
        ssvc_metric=SSVCMetric(
            exploitation=Exploitation.NONE,
            automatable=Automatable.NO,
            technical_impact=TechnicalImpact.PARTIAL,
            mission_impact=MissionImpact.LOW,
        ),
        owner="infra-tools-team",
        impact_score=15,
        likelihood_score=30,
        identified_date=today - timedelta(days=200),
        treatment_plan="Issue certificates from internal CA; automate renewal via ACME.",
        control_mapping=["NET-004"],
    ))

    r11 = add_to_register(register, create_risk(
        title="Non-Standard Port Exposure on DMZ Host",
        description=(
            "A DMZ jump host exposes SSH on TCP 2222 (non-standard) to the internet. "
            "While key-only authentication is enforced, the non-standard port bypasses "
            "the standard edge firewall rule set and could evade monitoring."
        ),
        category=RiskCategory.INFRASTRUCTURE,
        cvss_vector="AV:N/AC:H/PR:N/UI:N/S:U/C:L/I:N/A:N",
        ssvc_metric=SSVCMetric(
            exploitation=Exploitation.NONE,
            automatable=Automatable.NO,
            technical_impact=TechnicalImpact.PARTIAL,
            mission_impact=MissionImpact.LOW,
        ),
        owner="network-team",
        impact_score=20,
        likelihood_score=25,
        identified_date=today - timedelta(days=90),
        treatment_plan="Move SSH to internal-only access via VPN; close public port 2222.",
        control_mapping=["NET-001", "NET-002"],
    ))

    # --- 1 ACCEPTED risk ---

    r12 = add_to_register(register, create_risk(
        title="Legacy Mainframe — End-of-Support OS",
        description=(
            "The billing mainframe runs z/OS 2.3 which reached end-of-support in "
            "December 2024. IBM no longer provides security patches. Migration to "
            "z/OS 3.1 is planned but dependent on a COTS upgrade cycle in Q3 2026."
        ),
        category=RiskCategory.VENDOR,
        cvss_vector="AV:N/AC:H/PR:N/UI:N/S:U/C:H/I:H/A:H",
        ssvc_metric=SSVCMetric(
            exploitation=Exploitation.NONE,
            automatable=Automatable.NO,
            technical_impact=TechnicalImpact.TOTAL,
            mission_impact=MissionImpact.MEDIUM,
        ),
        owner="mainframe-team",
        impact_score=75,
        likelihood_score=20,
        identified_date=today - timedelta(days=365),
        treatment_plan="Isolate mainframe to dedicated VLAN; implement compensating controls.",
        control_mapping=["VEND-001", "NET-005"],
    ))
    accept_risk(
        r12,
        rationale=(
            "Migration blocked by COTS vendor timeline (SAP Billing 8.0 upgrade required "
            "first). Compensating controls (VLAN isolation, strict firewall rules, "
            "dedicated jump host) reduce residual risk to acceptable level. "
            "Board-approved acceptance per GRC-2025-042."
        ),
        accepted_by="cto",
        review_days=180,
    )

    # --- 1 MITIGATED risk ---

    r13 = add_to_register(register, create_risk(
        title="Third-Party SDK with Known XSS Vulnerability",
        description=(
            "The charting SDK used in the analytics dashboard (ChartMaster v4.1.0) "
            "contains a stored XSS vulnerability (CVE-2025-12345). Vendor released "
            "patch in v4.1.1."
        ),
        category=RiskCategory.VENDOR,
        cvss_vector="AV:N/AC:L/PR:N/UI:R/S:U/C:H/I:L/A:N",
        ssvc_metric=SSVCMetric(
            exploitation=Exploitation.ACTIVE,
            automatable=Automatable.YES,
            technical_impact=TechnicalImpact.PARTIAL,
            mission_impact=MissionImpact.HIGH,
        ),
        owner="eng-team",
        impact_score=60,
        likelihood_score=70,
        identified_date=today - timedelta(days=10),
        treatment_plan="Upgraded ChartMaster to v4.1.1; CSP header tightened to block inline scripts.",
        control_mapping=["APP-002", "VULN-003"],
    ))
    # Manually set status to MITIGATED (it went through the workflow)
    r13.status = RiskStatus.MITIGATED

    return register

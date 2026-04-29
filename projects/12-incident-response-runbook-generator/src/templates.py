"""Battle-tested incident response runbook templates.

Six incident types, each with six IR stages and 5+ detailed actions per stage.
These are the core intellectual property of the runbook generator.
"""

from .models import IRStage, RunbookTemplate

# ─────────────────────────────────────────────────────────────────
# Template: Malware Outbreak
# ─────────────────────────────────────────────────────────────────

MALWARE_STAGES = [
    IRStage(
        stage_number=1,
        stage_name="Identification",
        description="Detect and confirm the presence of malware within the environment through multiple detection signals.",
        actions=[
            "Acknowledge and triage antivirus/EDR alerts (CrowdStrike, Defender, SentinelOne) within 5 minutes of trigger",
            "Correlate alerts with SIEM (Splunk, Sentinel) to identify patient-zero endpoint and initial infection vector",
            "Review network traffic logs for command-and-control (C2) beaconing patterns to known malicious IPs/domains",
            "Interview affected users to confirm unusual system behaviour: pop-ups, performance degradation, unauthorised processes",
            "Capture forensic snapshot: running processes, network connections, registry keys, scheduled tasks on suspected hosts",
            "Declare incident severity based on blast radius: single host (SEV3), multiple hosts (SEV2), critical server/domain controller (SEV1)",
        ],
        responsible_team="SOC Tier 1 / Detection Engineering",
        sla_minutes=15,
        escalation_trigger="Malware confirmed on more than 3 hosts OR on any domain controller, file server, or PCI-scoped system",
    ),
    IRStage(
        stage_number=2,
        stage_name="Containment",
        description="Isolate affected systems to prevent lateral movement and further compromise.",
        actions=[
            "Network-isolate affected hosts at switch/EDR level -- do NOT power off (preserves memory forensics)",
            "Block identified command-and-control IPs and domains at perimeter firewall and web proxy (Zscaler, Netskope)",
            "Disable compromised user accounts and service accounts in Active Directory / Okta -- revoke all active sessions",
            "Disconnect affected network shares and disable file synchronisation to cloud storage (OneDrive, Google Drive, Dropbox)",
            "Apply EDR host containment: block outbound network connections except to management console, deny process creation from temporary directories",
            "Capture disk image and memory dump from patient-zero system for forensic analysis before initiating eradication",
        ],
        responsible_team="CSIRT / Infrastructure",
        sla_minutes=30,
        escalation_trigger="Malware spreading to additional hosts despite containment measures OR lateral movement to PCI/PII data stores detected",
    ),
    IRStage(
        stage_number=3,
        stage_name="Eradication",
        description="Remove all traces of malware from affected systems and close the infection vector.",
        actions=[
            "Execute EDR-initiated full system scan on all affected hosts with maximum sensitivity and cloud-based IOC lookup",
            "Manually review and remove persistence mechanisms: registry Run keys, scheduled tasks, WMI event subscriptions, startup folder entries",
            "Identify and patch the infection vector: phishing attachment (block sender domain), drive-by download (block URL), USB autorun (disable), vulnerable service (apply patch)",
            "Rotate all credentials that were active on compromised systems: user passwords, service account keys, API tokens, SSH keys",
            "Validate eradication by running secondary scan with a different AV engine (Malwarebytes, ESET Online Scanner) and reviewing process trees",
            "Restore or rebuild affected workstations from known-clean gold images -- do not reuse the compromised OS installation",
        ],
        responsible_team="CSIRT / Endpoint Engineering",
        sla_minutes=120,
        escalation_trigger="Re-infection detected after eradication steps completed OR persistence mechanism cannot be identified after 4 hours of analysis",
    ),
    IRStage(
        stage_number=4,
        stage_name="Recovery",
        description="Restore normal business operations and verify system integrity.",
        actions=[
            "Restore affected file shares and databases from last known-clean backup (verify backup integrity before restore -- check hash, scan with AV)",
            "Reconnect rebuilt endpoints to the network one at a time, monitoring EDR telemetry for 30 minutes before reconnecting the next",
            "Re-enable user accounts and service accounts with new credentials -- enforce password change on next login for all affected users",
            "Verify critical business application functionality: test payment processing, customer-facing portals, internal tools before declaring recovery complete",
            "Conduct post-recovery vulnerability scan of all reconnected systems to ensure no security gaps were introduced during rebuild",
            "Restore network share access and cloud sync with enhanced monitoring rules for the first 72 hours post-recovery",
        ],
        responsible_team="Infrastructure / Application Support",
        sla_minutes=180,
        escalation_trigger="Backup restoration fails OR reconnected endpoint triggers new EDR alert within monitoring window",
    ),
    IRStage(
        stage_number=5,
        stage_name="Post-Incident Analysis",
        description="Investigate root cause, document findings, and determine full scope of impact.",
        actions=[
            "Perform timeline reconstruction: map every attacker action from initial compromise to detection using SIEM, EDR, and network log correlation",
            "Conduct forensic analysis of captured disk/memory images to identify malware family, capabilities, and data exfiltration attempts",
            "Determine scope of data access: identify which files, databases, and systems the compromised accounts had access to during the incident window",
            "Calculate incident metrics: time-to-detect (TTD), time-to-contain (TTC), time-to-eradicate (TTE), systems affected, users impacted, data accessed",
            "Document the incident in a formal post-incident report with executive summary, technical timeline, IOC list, and remediation actions taken",
            "Submit IOCs (file hashes, C2 domains, IPs) to threat intelligence platform (MISP, ThreatConnect) and block across all security tooling",
        ],
        responsible_team="CSIRT / Threat Intelligence",
        sla_minutes=480,
        escalation_trigger="Evidence of data exfiltration discovered that was not previously identified OR attacker accessed regulatory-scoped data (PCI, PII, PHI)",
    ),
    IRStage(
        stage_number=6,
        stage_name="Lessons Learned & Closure",
        description="Drive organisational improvement from incident findings and formally close the incident.",
        actions=[
            "Facilitate a blameless post-mortem meeting with all involved teams within 5 business days of incident closure",
            "Identify and prioritise control gaps that allowed the incident: missing EDR coverage, unpatched systems, lack of application whitelisting, insufficient user awareness training",
            "Update detection engineering rules: create new SIEM correlation searches, EDR custom IOAs, and network IDS signatures based on observed TTPs",
            "Update runbook template with lessons learned: adjust SLAs, add new containment actions, refine escalation triggers based on actual incident performance",
            "Assign remediation owners and track corrective actions to completion in GRC platform or ticketing system (Jira, ServiceNow)",
            "Conduct targeted phishing simulation or user awareness session if the infection vector was human-initiated, and schedule follow-up assessment within 30 days",
            "Present incident summary and improvement plan to CISO / Security Steering Committee; obtain sign-off for formal closure",
        ],
        responsible_team="CISO Office / Security Governance",
        sla_minutes=10080,
        escalation_trigger="Control gap remediation not started within 30 days of incident closure OR repeat incident of same type occurs",
    ),
]

MALWARE_TEMPLATE = RunbookTemplate(
    incident_type="malware",
    base_stages=MALWARE_STAGES,
    default_contacts={
        "Incident Commander": {"name": "SOC Lead", "email": "soc-lead@company.com", "phone": "+1-555-0100"},
        "Technical Lead": {"name": "CSIRT Engineer", "email": "csirt@company.com", "phone": "+1-555-0101"},
        "Communications": {"name": "CISO Office", "email": "ciso-office@company.com", "phone": "+1-555-0102"},
        "Legal": {"name": "General Counsel", "email": "legal@company.com", "phone": "+1-555-0103"},
        "Executive Sponsor": {"name": "CISO", "email": "ciso@company.com", "phone": "+1-555-0104"},
    },
    default_tools=[
        {"name": "CrowdStrike Falcon", "purpose": "Endpoint detection and response, host isolation, IOC scanning"},
        {"name": "Splunk / SIEM", "purpose": "Log aggregation, correlation searches, timeline reconstruction"},
        {"name": "Zscaler / Web Proxy", "purpose": "Block malicious domains and IPs at the perimeter"},
        {"name": "Active Directory", "purpose": "Account disablement, group policy enforcement"},
        {"name": "PagerDuty", "purpose": "Incident alerting, on-call escalation, team mobilisation"},
        {"name": "Forensic Toolkit (FTK / Volatility)", "purpose": "Disk and memory forensics on compromised hosts"},
    ],
    default_comms=[
        "Initial notification: SOC Lead declares incident and notifies CSIRT via PagerDuty within 5 minutes of confirmation",
        "Hourly status update to CISO and affected business unit heads for first 4 hours, then every 4 hours until containment",
        "Customer/data subject notification if malware accessed PII/PCI data -- coordinate with Legal and DPO within 24 hours",
        "Regulatory notification to ICO/FCA if incident qualifies as notifiable breach under GDPR/NIS2 -- within 72 hours of discovery",
        "All-staff communication warning about phishing/attack vector if relevant, with clear instructions on what to look for and report",
    ],
)

# ─────────────────────────────────────────────────────────────────
# Template: Ransomware Attack
# ─────────────────────────────────────────────────────────────────

RANSOMWARE_STAGES = [
    IRStage(
        stage_number=1,
        stage_name="Identification",
        description="Detect ransomware activity through encryption alerts, user reports, and backup system anomalies.",
        actions=[
            "Acknowledge EDR ransomware protection alerts (behavioural detection of mass file modification, shadow copy deletion) within 3 minutes",
            "Triage user reports of inaccessible files, ransom notes (.txt/.html on desktop), or encrypted file extensions (.lockbit, .blackcat, .enc)",
            "Check backup systems (Veeam, Rubrik, Commvault) for mass deletion or modification of backup jobs and snapshot repositories",
            "Identify patient-zero by correlating file modification timestamps across file servers, NAS devices, and SharePoint/OneDrive",
            "Review network traffic for SMB propagation patterns (rapid sequential connections to multiple hosts on port 445) and data staging behaviour",
            "Declare incident: if encryption confirmed on any production system, declare SEV1 immediately -- ransomware requires maximum urgency regardless of blast radius",
        ],
        responsible_team="SOC Tier 1 / Detection Engineering",
        sla_minutes=15,
        escalation_trigger="Ransomware encryption confirmed on any system -- immediate SEV1 declaration and full CSIRT mobilisation",
    ),
    IRStage(
        stage_number=2,
        stage_name="Containment",
        description="Stop encryption spread and prevent data exfiltration while preserving forensic evidence.",
        actions=[
            "Execute emergency network isolation: disable all outbound internet access from affected network segments at the core switch/router level",
            "Disable all domain admin, service, and user accounts that showed activity in the 24 hours preceding the incident -- force organisation-wide password reset",
            "Shut down or suspend all backup systems and disconnect backup storage from the network to prevent encryption/deletion of recovery data",
            "Preserve encrypted file samples, ransom note contents, and cryptocurrency wallet addresses for law enforcement and threat intelligence sharing",
            "Isolate affected systems from the network but do NOT power off -- ransomware may trigger additional damage routines on reboot (e.g., NotPetya-style)",
            "Engage external incident response firm if the organisation does not have 24/7 ransomware negotiation and decryption capability in-house",
        ],
        responsible_team="CSIRT / Infrastructure",
        sla_minutes=30,
        escalation_trigger="Encryption spreading to backup infrastructure OR ransom note contains credible data exfiltration threat with proof-of-life samples",
    ),
    IRStage(
        stage_number=3,
        stage_name="Eradication",
        description="Eliminate ransomware presence and prevent reinfection.",
        actions=[
            "Rebuild ALL affected servers and workstations from known-clean golden images or infrastructure-as-code templates -- never attempt to clean a ransomed system in place",
            "Rotate EVERY credential in the environment: domain admin passwords, service accounts, local admin passwords (LAPS), API keys, SSH keys, VPN certificates, and cloud IAM access keys",
            "Identify and close initial access vector: review VPN logs for brute-force/dumped credentials, RDP exposure, phishing campaign timeline, unpatched public-facing vulnerability (CVE mapping)",
            "Deploy enhanced EDR policy to all endpoints: enable aggressive ransomware protection mode, block execution from %APPDATA% and %TEMP%, restrict PowerShell to constrained language mode",
            "Validate eradication by running threat-hunting queries across the environment for 24 hours post-rebuild, searching for IOCs, persistence mechanisms, and lateral movement artefacts",
            "If decryption was negotiated: isolate decryption tool in a sandboxed environment, validate it on test VMs before deploying to production, and scan recovered files for secondary payloads",
        ],
        responsible_team="CSIRT / Endpoint Engineering",
        sla_minutes=240,
        escalation_trigger="Ransomware group re-encrypts systems after initial recovery OR negotiation/decryption process deadlocked after 48 hours",
    ),
    IRStage(
        stage_number=4,
        stage_name="Recovery",
        description="Restore operations from clean backups and validate business function restoration.",
        actions=[
            "Restore data from offline/immutable backups -- prioritise by business criticality: Tier 1 (revenue-generating, patient safety) first, Tier 2 (internal operations) second, Tier 3 (non-critical) last",
            "Verify backup integrity before restore: check cryptographic signatures, scan restored files with multiple AV engines, validate against known-good file hashes where available",
            "Rebuild and reconnect systems in a phased approach: domain controllers first, then application servers, then databases, then file servers, then end-user workstations",
            "Run full regression tests on all recovered applications: validate payment processing, customer data integrity, report generation, API integrations",
            "Deploy additional monitoring: enable enhanced Windows Event Log collection (4688 process creation, 5145 file share access, 4663 object access), ship to SIEM with real-time alerting",
            "Communicate restoration status to stakeholders at each phase completion -- provide estimated timelines for each subsequent recovery wave",
        ],
        responsible_team="Infrastructure / Application Support",
        sla_minutes=480,
        escalation_trigger="Critical backup repository found encrypted or corrupted OR Tier 1 application restoration fails after two attempts",
    ),
    IRStage(
        stage_number=5,
        stage_name="Post-Incident Analysis",
        description="Conduct comprehensive forensic investigation and assess full business impact.",
        actions=[
            "Perform end-to-end timeline reconstruction from initial access to containment, mapping every attacker TTP using MITRE ATT&CK framework",
            "Engage threat intelligence partners to attribute ransomware variant to known group, understand their TTPs, and assess likelihood of re-targeting",
            "Assess data exfiltration scope: analyse network flow logs for large outbound transfers in the 72 hours preceding encryption, review cloud access logs for unauthorised downloads",
            "Calculate full business impact: systems affected, data encrypted/exfiltrated, downtime duration, revenue loss estimate, regulatory exposure, reputational impact",
            "Notify law enforcement (FBI IC3 / Europol / NCA) and provide IOCs, wallet addresses, and ransom note copies -- coordinate with cyber insurance carrier for loss assessment",
            "Produce formal post-incident report with executive summary, technical root cause analysis, MITRE ATT&CK mapping, data exposure assessment, and regulatory notification status",
        ],
        responsible_team="CSIRT / Threat Intelligence",
        sla_minutes=1440,
        escalation_trigger="Evidence of data exfiltration to adversarial infrastructure OR regulatory body (ICO, FCA, SEC) opens formal investigation",
    ),
    IRStage(
        stage_number=6,
        stage_name="Lessons Learned & Closure",
        description="Rebuild resilience and close control gaps that enabled the ransomware attack.",
        actions=[
            "Conduct mandatory blameless post-mortem with all teams within 10 business days, including external IR firm if engaged",
            "Implement offline/immutable backup strategy: air-gapped backup copies, write-once-read-many (WORM) storage, separate backup authentication domain",
            "Review and harden Active Directory security: tiered admin model (Tier 0/1/2), LAPS deployment, BloodHound audit for attack paths, disable NTLM where possible",
            "Enhance email security: deploy DMARC/DKIM/SPF enforcement, advanced phishing protection (Abnormal Security, Proofpoint), disable macros in Office documents from external sources",
            "Evaluate cyber insurance coverage adequacy post-incident and update policy limits, coverage scope, and approved IR vendor panel",
            "Update ransomware runbook with variant-specific IOCs, TTPs observed, decryption resources (No More Ransom Project), and any effective containment measures discovered during the incident",
            "Conduct board-level review of ransomware resilience programme: backup testing cadence, tabletop exercise frequency, security investment priorities, and risk acceptance decisions",
        ],
        responsible_team="CISO Office / Security Governance",
        sla_minutes=20160,
        escalation_trigger="Repeat ransomware attempt within 90 days OR board does not approve recommended remediation investment within one quarter",
    ),
]

RANSOMWARE_TEMPLATE = RunbookTemplate(
    incident_type="ransomware",
    base_stages=RANSOMWARE_STAGES,
    default_contacts={
        "Incident Commander": {"name": "CISO", "email": "ciso@company.com", "phone": "+1-555-0200"},
        "Technical Lead": {"name": "IR Lead", "email": "ir-lead@company.com", "phone": "+1-555-0201"},
        "Communications": {"name": "VP Communications", "email": "comms@company.com", "phone": "+1-555-0202"},
        "Legal": {"name": "General Counsel", "email": "legal@company.com", "phone": "+1-555-0203"},
        "Cyber Insurance": {"name": "Risk Manager", "email": "risk@company.com", "phone": "+1-555-0204"},
        "External IR Firm": {"name": "IR Retainer", "email": "ir-oncall@external-firm.com", "phone": "+1-800-555-0205"},
        "Law Enforcement": {"name": "FBI IC3 / NCA Liaison", "email": "cyber@ic3.gov", "phone": "+1-800-CALL-FBI"},
    },
    default_tools=[
        {"name": "CrowdStrike Falcon / EDR", "purpose": "Ransomware behavioural detection, host isolation, real-time response"},
        {"name": "Splunk / SIEM", "purpose": "Centralised logging, correlation, timeline reconstruction"},
        {"name": "Veeam / Backup System", "purpose": "Immutable backup verification and restoration"},
        {"name": "Active Directory", "purpose": "Account lockout, credential rotation, tiered admin enforcement"},
        {"name": "No More Ransom Project", "purpose": "Free decryption tools for known ransomware families"},
        {"name": "ID Ransomware", "purpose": "Ransomware variant identification from ransom note and encrypted file samples"},
    ],
    default_comms=[
        "Immediate SEV1 declaration to CISO, CIO, CEO, General Counsel via PagerDuty emergency channel",
        "All-hands bridge (Zoom/Teams with recording) established within 15 minutes of confirmation",
        "Regulatory notification to ICO/FCA if personal/financial data encrypted or exfiltrated -- within 72 hours of discovery",
        "Customer notification if service delivery impacted beyond SLA -- coordinate with Customer Success and PR teams",
        "Board update within 24 hours: incident summary, containment status, recovery timeline, regulatory/legal status",
        "Media statement prepared by Communications team in coordination with legal counsel -- do NOT comment on ransom demands publicly",
    ],
)

# ─────────────────────────────────────────────────────────────────
# Template: Data Breach
# ─────────────────────────────────────────────────────────────────

BREACH_STAGES = [
    IRStage(
        stage_number=1,
        stage_name="Identification",
        description="Detect and confirm unauthorised access to or exfiltration of sensitive data.",
        actions=[
            "Triage DLP alerts indicating bulk data transfer, unusual file access patterns, or data classified above user clearance level being accessed",
            "Investigate SIEM alerts for anomalous database queries (SELECT *, large result sets), cloud storage API calls (S3 GetObject spikes, Azure Blob downloads), and email attachment rules",
            "Review dark web monitoring feeds (Recorded Future, Digital Shadows) for organisation-specific data appearing on paste sites, forums, or marketplaces",
            "Correlate access logs from data stores (SQL Server audit logs, AWS CloudTrail, SharePoint audit logs) with identity provider logs (Okta, Azure AD) to identify the actor",
            "Verify whether accessed data contains PII, PCI, PHI, or IP using data classification tags and data catalog metadata (Collibra, Alation, AWS Glue)",
            "Declare severity based on data type and volume: PII < 1000 records (SEV3), PII 1000-100k or PCI (SEV2), PII > 100k, PHI, or IP (SEV1)",
        ],
        responsible_team="SOC Tier 1 / DLP Operations",
        sla_minutes=15,
        escalation_trigger="Confirmed exfiltration of PII/PCI/PHI/IP data OR data appears on dark web monitoring platforms",
    ),
    IRStage(
        stage_number=2,
        stage_name="Containment",
        description="Stop ongoing data loss and preserve forensic evidence for investigation.",
        actions=[
            "Immediately revoke access for the compromised identity: disable user account, revoke API keys and OAuth tokens, expire active sessions in IdP",
            "Apply network restrictions to block data exfiltration channels: block outbound connections to known exfiltration IPs, restrict cloud storage sharing to internal-only",
            "Preserve all logs related to the incident: database audit logs, identity provider sign-in logs, cloud storage access logs, email gateway logs, DLP incident records",
            "Issue litigation hold on all mailboxes, SharePoint sites, and cloud storage accounts associated with the compromised identity",
            "Disable external sharing on all cloud storage platforms (OneDrive, Google Drive, Box, Dropbox) for the affected user population pending review",
            "Engage privacy legal counsel and Data Protection Officer (DPO) immediately -- data breach notification obligations are time-sensitive under GDPR (72 hours), state breach laws, and PCI-DSS",
        ],
        responsible_team="CSIRT / Identity Management",
        sla_minutes=30,
        escalation_trigger="Data exfiltration ongoing at time of detection OR breach involves special category data (health, biometric, children, criminal)",
    ),
    IRStage(
        stage_number=3,
        stage_name="Eradication",
        description="Identify exfiltrated data scope, close the entry point, and prevent further unauthorised access.",
        actions=[
            "Map exact scope of exfiltrated data: which databases, tables, files, mailboxes were accessed -- use database audit logs, file access timestamps, and email journal records",
            "Identify and close the entry point: compromised credentials (force reset all sessions), misconfigured S3 bucket (apply proper policy), SQL injection (patch and validate), insider abuse (legal hold)",
            "Review all recent access for the compromised identity and any identities with similar access patterns or privilege levels -- expand investigation if anomalous access is found",
            "Engage external forensics firm if the breach scope exceeds internal investigation capability or if forensic evidence preservation is required for potential litigation",
            "Classify exfiltrated data fields precisely: names, addresses, SSN/NI numbers, payment card data (PAN, CVV, expiry), health records, credentials (passwords, tokens), IP/trade secrets",
            "Determine whether encryption was applied to exfiltrated data at rest and in transit -- this directly impacts regulatory notification obligations under GDPR (Article 34)",
        ],
        responsible_team="CSIRT / Data Governance",
        sla_minutes=180,
        escalation_trigger="Breach scope expands beyond initially identified data OR evidence suggests attacker still has access via undetected persistence",
    ),
    IRStage(
        stage_number=4,
        stage_name="Recovery",
        description="Execute notification protocol and implement measures to protect affected individuals.",
        actions=[
            "Prepare regulatory notification to relevant authorities: ICO (UK GDPR), relevant EU DPA (EU GDPR), FTC/SEC (US), FCA (UK financial services) -- provide breach description, data categories, affected count, mitigation measures",
            "Prepare data subject notification: clear, plain-language communication explaining what happened, what data was involved, what the organisation is doing, and what steps affected individuals should take (credit monitoring, password change, fraud alert)",
            "Engage credit monitoring and identity theft protection service for affected individuals (Experian, Equifax, LifeLock) -- minimum 12 months coverage for PII breaches",
            "Set up dedicated incident response hotline and email for affected individuals to ask questions and report concerns",
            "Restore secure access to affected data stores with enhanced monitoring: enable real-time alerting on bulk data access, implement just-in-time access for privileged roles, enable data access logging with immutable storage",
            "Coordinate with PR/Communications team on public statement if breach exceeds regulatory disclosure thresholds or media coverage is expected",
        ],
        responsible_team="Privacy Legal / DPO / Communications",
        sla_minutes=240,
        escalation_trigger="Media inquiry received before notification prepared OR regulatory authority requests immediate briefing",
    ),
    IRStage(
        stage_number=5,
        stage_name="Post-Incident Analysis",
        description="Conduct root cause analysis and assess full regulatory and business impact.",
        actions=[
            "Perform detailed root cause analysis: reconstruct data access timeline, identify why existing controls (DLP, access reviews, encryption) failed to prevent or detect the breach",
            "Map the incident to applicable regulatory frameworks: GDPR (Articles 33/34 notification), PCI-DSS (requirement 12.10 incident response), NIS2 (Article 23 reporting), SOX (disclosure controls), state breach notification laws",
            "Calculate breach metrics: records affected, data subjects by jurisdiction, time from breach to detection, time from detection to containment, notification timelines met/missed",
            "Assess regulatory fine exposure: GDPR (up to 4% global annual turnover or EUR20M), FCA enforcement action, PCI-DSS non-compliance penalties, class-action litigation risk",
            "Submit data breach report to cyber insurance carrier within policy notification window and coordinate with breach coach/legal panel counsel",
            "Document all evidence preservation steps for potential regulatory investigation or litigation discovery -- maintain chain of custody documentation for all forensic evidence",
        ],
        responsible_team="Privacy Legal / DPO / CSIRT",
        sla_minutes=720,
        escalation_trigger="Regulatory authority opens formal investigation OR class-action lawsuit filed OR material impact on share price",
    ),
    IRStage(
        stage_number=6,
        stage_name="Lessons Learned & Closure",
        description="Drive data protection improvements and close gaps that allowed the breach.",
        actions=[
            "Conduct blameless post-mortem focused on control failures: data classification gaps, access review deficiencies, DLP misconfiguration, encryption gaps, monitoring blind spots",
            "Implement data-centric security improvements: enhance data classification programme, deploy CASB for cloud data visibility, implement rights management (Azure RMS, AWS Macie), enforce just-in-time access for sensitive data",
            "Update data retention and minimisation policies: review whether exfiltrated data should have been deleted per retention schedule, implement automated data lifecycle management",
            "Conduct privacy impact assessment (PIA/DPIA) review cycle for all systems processing personal data -- ensure risk assessments reflect the newly understood threat scenario",
            "Enhance DLP monitoring: tune rules to detect exfiltration patterns identified in this incident, deploy UEBA for baseline anomaly detection on data access patterns",
            "Schedule independent audit of data protection controls (ISO 27701, SOC 2 Type II, PCI-DSS ROC) within 6 months of incident closure",
            "Present incident findings, regulatory exposure assessment, and remediation programme to Board / Audit Committee -- obtain sign-off on resource commitments for control improvements",
        ],
        responsible_team="CISO Office / Privacy Legal / Data Governance",
        sla_minutes=14400,
        escalation_trigger="Regulatory fine or enforcement action announced OR board rejects recommended data protection investment",
    ),
]

BREACH_TEMPLATE = RunbookTemplate(
    incident_type="breach",
    base_stages=BREACH_STAGES,
    default_contacts={
        "Incident Commander": {"name": "CISO", "email": "ciso@company.com", "phone": "+1-555-0300"},
        "Data Protection Officer": {"name": "DPO", "email": "dpo@company.com", "phone": "+1-555-0301"},
        "Privacy Legal Counsel": {"name": "Privacy Counsel", "email": "privacy-legal@company.com", "phone": "+1-555-0302"},
        "Technical Lead": {"name": "CSIRT Lead", "email": "csirt@company.com", "phone": "+1-555-0303"},
        "Communications": {"name": "VP Communications", "email": "comms@company.com", "phone": "+1-555-0304"},
        "Regulatory Liaison": {"name": "Head of Compliance", "email": "compliance@company.com", "phone": "+1-555-0305"},
    },
    default_tools=[
        {"name": "DLP Platform (Symantec / Forcepoint)", "purpose": "Detect and block sensitive data exfiltration across email, web, and endpoints"},
        {"name": "Splunk / SIEM", "purpose": "Log correlation across database, identity, network, and cloud access logs"},
        {"name": "Recorded Future / Digital Shadows", "purpose": "Dark web monitoring for exposed organisational data"},
        {"name": "AWS CloudTrail / Azure Monitor", "purpose": "Cloud API access logging and anomaly detection"},
        {"name": "Okta / Azure AD", "purpose": "Identity provider -- session revocation, access review, sign-in log analysis"},
        {"name": "Collibra / Data Catalog", "purpose": "Data classification and sensitive data inventory lookup"},
    ],
    default_comms=[
        "DPO notified within 30 minutes of breach confirmation -- DPO leads regulatory notification timeline",
        "Regulatory notification to ICO (UK GDPR) within 72 hours of discovery if risk to data subject rights and freedoms",
        "Data subject notification without undue delay if breach poses high risk (GDPR Article 34) -- DPO and Privacy Legal to determine timing",
        "PCI-DSS breach notification to acquiring bank and card brands within 24 hours if cardholder data involved",
        "Internal communication to Board, Audit Committee, and relevant business unit leads on need-to-know basis",
        "Public statement prepared and held ready for release -- coordinate timing with regulatory notifications to avoid premature disclosure",
    ],
)

# ─────────────────────────────────────────────────────────────────
# Template: DDoS Attack
# ─────────────────────────────────────────────────────────────────

DDOS_STAGES = [
    IRStage(
        stage_number=1,
        stage_name="Identification",
        description="Detect and characterise a distributed denial-of-service attack against infrastructure.",
        actions=[
            "Acknowledge monitoring alerts: CDN/WAF traffic spike exceeding baseline (300%+ normal), origin server CPU/memory saturation, elevated 5xx error rates, increased latency above SLA threshold",
            "Verify attack vs. legitimate traffic surge: check for marketing campaign, product launch, seasonal event, or viral content that could explain the traffic increase before declaring DDoS",
            "Characterise attack vector: volumetric (SYN flood, UDP flood, DNS amplification), protocol (SYN-ACK reflection, Ping of Death), application layer (HTTP flood, Slowloris, XML-RPC amplification)",
            "Identify target resources: specific URL endpoints, IP addresses, or domain names under attack -- determine whether the attack targets a single service or spans multiple assets",
            "Capture attack traffic samples using tcpdump, NetFlow/sFlow data, and WAF logs for forensic analysis and ISP/mitigation provider escalation",
            "Declare severity based on customer impact: non-critical internal system (SEV3), degraded customer-facing service (SEV2), complete outage of revenue-generating service (SEV1)",
        ],
        responsible_team="SOC Tier 1 / NOC",
        sla_minutes=10,
        escalation_trigger="Customer-facing service degraded beyond SLA OR attack volume approaching provisioned bandwidth/DDoS mitigation capacity",
    ),
    IRStage(
        stage_number=2,
        stage_name="Containment",
        description="Mitigate attack impact while maintaining legitimate user access.",
        actions=[
            "Engage DDoS mitigation provider (Cloudflare, AWS Shield Advanced, Akamai, Azure DDoS Protection) -- activate scrubbing centre or advanced mitigation mode if not already in always-on configuration",
            "Deploy rate limiting at WAF/CDN layer: implement per-IP and per-session rate limits, challenge可疑 traffic with JS challenge or CAPTCHA, geo-block if attack originates from specific regions not serving legitimate users",
            "Update WAF rules to block attack signatures: rate-limit specific URL patterns being targeted, block user-agents associated with attack tools, create custom规则 for application-layer attack patterns",
            "Blackhole or null-route attack traffic upstream at ISP/transit provider level if attack volume exceeds mitigation provider capacity -- accept that legitimate traffic will also be dropped as last resort",
            "Scale up origin infrastructure: deploy additional application server instances, enable auto-scaling with aggressive thresholds, increase load balancer connection limits",
            "Enable degraded/static mode for non-critical features: serve cached static versions of high-traffic pages, disable search/dynamic features temporarily, redirect non-essential traffic to status page",
        ],
        responsible_team="Infrastructure / SRE / Network Engineering",
        sla_minutes=30,
        escalation_trigger="Attack volume exceeds 80% of provisioned mitigation capacity OR legitimate users unable to access service despite mitigation measures",
    ),
    IRStage(
        stage_number=3,
        stage_name="Eradication",
        description="Eliminate the attack traffic at source and harden defences.",
        actions=[
            "Work with upstream ISPs and transit providers to block attack source IP ranges and ASNs at the BGP level using RTBH (Remotely Triggered Black Hole) filtering",
            "Configure or enhance DDoS mitigation provider protection: enable adaptive threat detection, deploy custom mitigation templates tuned to observed attack patterns, increase scrubbing capacity if necessary",
            "Identify and patch any application vulnerabilities being exploited: slow POST acceptance, XML entity expansion, unauthenticated expensive API endpoints, lack of request size limits",
            "Block identified attack IPs, CIDR ranges, and autonomous system numbers (ASNs) at the edge firewall and CDN -- maintain blocklist for minimum 30 days post-attack",
            "Deploy additional anycast distribution points if the attack is geographically concentrated -- spread traffic load across more points of presence",
            "Review and adjust origin IP exposure: ensure origin servers are not publicly discoverable (hide behind CDN, use non-standard ports, implement IP whitelisting for CDN backends only)",
        ],
        responsible_team="Network Engineering / SRE",
        sla_minutes=120,
        escalation_trigger="Attack evolves to bypass deployed mitigations OR multiple attack vectors combined simultaneously (multi-vector DDoS)",
    ),
    IRStage(
        stage_number=4,
        stage_name="Recovery",
        description="Gradually restore full service functionality while monitoring for attack resurgence.",
        actions=[
            "Gradually reduce rate limiting and security challenge thresholds in 25% increments every 15 minutes, monitoring for attack traffic resurgence at each step",
            "Restore full application functionality: re-enable dynamic features, search, user registration, and other services that were disabled during degraded mode",
            "Verify all origin servers are healthy: check CPU, memory, connection pool utilisation return to baseline -- replace any servers that show residual performance degradation",
            "Monitor CDN/WAF telemetry for 4 hours after full restoration with enhanced alerting thresholds (alert at 150% baseline rather than 300%)",
            "Communicate restoration to stakeholders: notify customer support team, update status page, inform key customers/partners if they were affected",
            "Conduct post-recovery performance test from multiple geographic regions to ensure latency and availability have returned to normal levels",
        ],
        responsible_team="Infrastructure / SRE / Customer Support",
        sla_minutes=120,
        escalation_trigger="Attack traffic resurges during ramp-up OR origin infrastructure shows signs of residual compromise from companion attack",
    ),
    IRStage(
        stage_number=5,
        stage_name="Post-Incident Analysis",
        description="Analyse attack characteristics, assess business impact, and determine attacker motivation.",
        actions=[
            "Perform detailed attack analysis: total attack volume (Gbps/Mpps), attack duration, primary attack vectors, geographic origin of attack traffic, botnet/malware family indicators",
            "Map attack timeline: precise start time, peak traffic point, mitigation deployment milestones, service degradation intervals, full restoration time -- produce attack timeline visualisation",
            "Calculate business impact: total downtime/duration, estimated revenue loss (peak-hour transactions lost x average transaction value), customer support ticket volume, SLA credit liability",
            "Investigate attack motivation: hacktivism (aligned with organisation's industry/actions), extortion (received threat preceding attack), competitive (competitor launch or event), distraction (cover for data breach attempt)",
            "Review DDoS mitigation provider performance: time-to-mitigate, false positive rate (legitimate traffic blocked), scrubbing effectiveness -- assess whether current tier of service is adequate",
            "Share attack indicators (signature patterns, source IPs, tools observed) with industry ISAC (FS-ISAC for financial services, NH-ISAC for healthcare) and threat intelligence platforms",
        ],
        responsible_team="CSIRT / SRE / Threat Intelligence",
        sla_minutes=360,
        escalation_trigger="Evidence of companion data breach during DDoS distraction OR extortion demand received with credible threat of follow-up attack",
    ),
    IRStage(
        stage_number=6,
        stage_name="Lessons Learned & Closure",
        description="Improve DDoS resilience and capacity planning based on real-world attack data.",
        actions=[
            "Conduct post-mortem with Infrastructure, SRE, NOC, and CDN/mitigation provider representation -- review every phase of the incident against the runbook",
            "Reassess DDoS mitigation capacity: compare attack peak against provisioned capacity, evaluate whether to upgrade to always-on mitigation, increase scrubbing centre bandwidth, or add secondary mitigation provider for redundancy",
            "Update capacity planning models: incorporate real-world attack volume data into infrastructure scaling plans, CDN bandwidth commitments, and ISP transit agreements",
            "Enhance monitoring: deploy flow-based detection (NetFlow/sFlow/IPFIX) with automated alerting at 150% baseline, implement synthetic transaction monitoring during attack conditions, add DDoS-specific dashboards to NOC wall displays",
            "Update application architecture for DDoS resilience: implement request queuing, graceful degradation paths, static page failover, and cache-first design patterns for critical user journeys",
            "Conduct DDoS tabletop exercise within 60 days using the updated runbook -- test team response time, mitigation provider coordination, and communication plan execution",
            "Review DDoS protection budget against actual business impact and present business case for additional investment to CTO/CFO if warranted",
        ],
        responsible_team="CISO Office / Infrastructure / SRE Leadership",
        sla_minutes=10080,
        escalation_trigger="Repeat DDoS attack within 30 days OR capacity planning assessment reveals insufficient protection for likely attack scenarios",
    ),
]

DDOS_TEMPLATE = RunbookTemplate(
    incident_type="ddos",
    base_stages=DDOS_STAGES,
    default_contacts={
        "Incident Commander": {"name": "Head of Infrastructure", "email": "infra-lead@company.com", "phone": "+1-555-0400"},
        "Network Lead": {"name": "Network Engineering Lead", "email": "neteng@company.com", "phone": "+1-555-0401"},
        "SRE Lead": {"name": "SRE Manager", "email": "sre@company.com", "phone": "+1-555-0402"},
        "CDN/Mitigation Provider": {"name": "Provider TAM", "email": "support@cdn-provider.com", "phone": "+1-800-555-0403"},
        "ISP/NOC Liaison": {"name": "ISP NOC", "email": "noc@isp.com", "phone": "+1-555-0404"},
        "Communications": {"name": "VP Engineering", "email": "eng-comms@company.com", "phone": "+1-555-0405"},
    },
    default_tools=[
        {"name": "Cloudflare / Akamai / AWS Shield", "purpose": "DDoS mitigation -- traffic scrubbing, rate limiting, WAF rules"},
        {"name": "Datadog / Grafana / CloudWatch", "purpose": "Infrastructure monitoring, traffic baselining, alerting"},
        {"name": "PagerDuty", "purpose": "Incident alerting, on-call escalation, team mobilisation"},
        {"name": "Wireshark / tcpdump", "purpose": "Packet capture and attack traffic analysis"},
        {"name": "NetFlow / sFlow Collector", "purpose": "Flow-based traffic analysis and attack vector identification"},
        {"name": "StatusPage / ServiceNow", "purpose": "Public status communication and internal incident tracking"},
    ],
    default_comms=[
        "NOC declares incident and pages Infrastructure/SRE on-call within 5 minutes of detection",
        "Status page updated with incident notice within 15 minutes -- updated every 30 minutes during active incident",
        "Customer support team briefed with template response and escalation path for customer inquiries",
        "Key enterprise customers notified by Customer Success team if their services are specifically affected",
        "All-clear communication sent to all stakeholders when service fully restored with post-incident summary within 24 hours",
    ],
)

# ─────────────────────────────────────────────────────────────────
# Template: Insider Threat
# ─────────────────────────────────────────────────────────────────

INSIDER_STAGES = [
    IRStage(
        stage_number=1,
        stage_name="Identification",
        description="Detect indicators of malicious insider activity or compromised insider credentials.",
        actions=[
            "Triage UEBA alerts for anomalous user behaviour: unusual after-hours access, impossible travel (geolocation anomalies), first-time access to sensitive data repositories, sudden increase in data download volume",
            "Review DLP alerts triggered by the user: bulk file downloads to USB, large email attachments to personal addresses, printing of sensitive documents, uploading to unsanctioned cloud storage (Dropbox, Google Drive personal)",
            "Correlate HR trigger events with the activity timeline: resignation submitted, performance improvement plan issued, role change denied, contract non-renewal, disciplinary action -- these are strong insider threat indicators",
            "Analyse access badge and physical security logs: unusual building access times, accessing floors/zones not required for role, tailgating patterns, attempts to access secure areas (data centre, executive offices)",
            "Review VPN and remote access logs: connections from unusual geolocations, connections at unusual hours, use of personal devices (BYOD) for accessing sensitive systems",
            "Declare severity based on data sensitivity and exfiltration evidence: policy violation (SEV3), unauthorised access to confidential data (SEV2), confirmed data exfiltration or sabotage (SEV1)",
        ],
        responsible_team="SOC Tier 1 / UEBA Monitoring",
        sla_minutes=30,
        escalation_trigger="Confirmed data exfiltration to external destination OR activity involves sabotage of critical systems OR user is a privileged administrator",
    ),
    IRStage(
        stage_number=2,
        stage_name="Containment",
        description="Suspend insider access and preserve evidence while maintaining legal and HR compliance.",
        actions=[
            "Coordinate with HR and Legal BEFORE taking action -- insider investigations have employment law implications; ensure proper authorisation and documentation throughout",
            "Suspend all system access for the individual: disable AD/Okta account, revoke VPN certificates, disable building access badge, revoke cloud IAM roles and API keys",
            "Do NOT confront the individual if criminal activity is suspected -- preserve surprise for potential law enforcement search and seizure; maintain business-as-usual appearance",
            "Preserve all evidence with forensic integrity: image the individual's workstation(s), capture email mailbox (litigation hold), download cloud storage contents, preserve VPN and access logs with chain of custody documentation",
            "Place legal hold on all data associated with the individual: email, file shares, cloud storage, code repositories, database access logs, CRM records -- prevent any automated deletion or retention policy application",
            "Monitor for dormant accounts, backdoor accounts, or privilege escalation that the insider may have created -- review recent account creation and privilege modification logs for the past 90 days",
        ],
        responsible_team="CSIRT / HR / Legal",
        sla_minutes=60,
        escalation_trigger="Individual is a senior executive or system administrator with extensive access OR evidence of collusion with external parties",
    ),
    IRStage(
        stage_number=3,
        stage_name="Eradication",
        description="Audit access, identify data exfiltration scope, and close unauthorised access paths.",
        actions=[
            "Conduct comprehensive access review for the individual: enumerate every system, application, database, file share, and cloud resource they had access to -- identify what was actually accessed in the preceding 90 days",
            "Map data accessed against data classification: determine whether PII, PCI, PHI, IP, trade secrets, or financial data was accessed -- quantify records/files affected",
            "Identify and revoke any shared accounts, service accounts, API keys, or SSH keys known or suspected to be known by the individual",
            "Audit data egress channels used: email (search for large attachments to personal addresses), USB (endpoint DLP logs), cloud upload (CASB logs), printer (print server logs), physical removal (inventory checks of company assets assigned to individual)",
            "Review code repository activity for unauthorised changes, backdoors inserted, or intellectual property downloaded in bulk from GitHub/GitLab/Bitbucket",
            "Assess whether the individual created or modified any automation (cron jobs, scheduled tasks, CI/CD pipelines) that could persist after account suspension and provide ongoing unauthorised access",
        ],
        responsible_team="CSIRT / Data Governance / Application Owners",
        sla_minutes=240,
        escalation_trigger="Intellectual property or trade secrets confirmed exfiltrated OR evidence of sabotage to production systems or data integrity",
    ),
    IRStage(
        stage_number=4,
        stage_name="Recovery",
        description="Restore affected data, notify stakeholders, and return to normal operations.",
        actions=[
            "Restore or rollback any data, code, or configurations that were modified, deleted, or corrupted by the insider -- use verified backups or version control history",
            "Reassign the individual's active projects, tickets, and responsibilities to other team members -- ensure business continuity for any processes dependent on the individual's access or knowledge",
            "Conduct broader team access review: check whether the insider's direct colleagues exhibited similar anomalous behaviour or had their credentials compromised",
            "Notify affected stakeholders on a need-to-know basis: impacted clients if their data was accessed, regulators if the incident triggers notification obligations, insurance carrier if coverage may apply",
            "Reset shared credentials and service account passwords for any systems the individual had access to -- implement new secrets in a phased approach to avoid service disruption",
            "Brief the individual's manager and team on the situation (within the bounds of HR/Legal guidance) and provide support resources if the insider was acting under duress or coercion",
        ],
        responsible_team="HR / Legal / Application Support",
        sla_minutes=480,
        escalation_trigger="Evidence that insider collaborated with external threat actor OR data exfiltration involved regulated data requiring breach notification",
    ),
    IRStage(
        stage_number=5,
        stage_name="Post-Incident Analysis",
        description="Investigate root cause, motive, and control failures that enabled the insider threat.",
        actions=[
            "Conduct thorough investigation of the individual's activity: reconstruct full timeline of actions from 90 days prior to detection, identify motive (financial gain, grievance, espionage, coercion), and determine whether others were involved",
            "Engage external forensic investigator if criminal prosecution is anticipated -- ensure all evidence handling meets criminal evidentiary standards (A CPR guidelines in UK, Federal Rules of Evidence in US)",
            "File law enforcement report if criminal activity is confirmed: economic espionage, theft of trade secrets, fraud, computer misuse act violations -- coordinate with Legal on timing and content",
            "Assess HR process failures: were red flags missed during recruitment (background check gaps), during employment (performance/behavioural indicators not escalated), or during departure (offboarding delays, access not fully revoked)",
            "Evaluate technical control failures: why didn't DLP block the exfiltration, why didn't UEBA detect the anomaly sooner, why wasn't privileged access reviewed/recertified on schedule",
            "Produce confidential post-incident report for CISO, CHRO, and General Counsel with full findings, root cause analysis, control gaps identified, and legal/HR recommendations",
        ],
        responsible_team="CSIRT / HR / Legal",
        sla_minutes=720,
        escalation_trigger="Criminal prosecution being pursued OR media/regulatory inquiry received OR whistleblower retaliation claim raised",
    ),
    IRStage(
        stage_number=6,
        stage_name="Lessons Learned & Closure",
        description="Strengthen insider threat programme and close procedural and technical control gaps.",
        actions=[
            "Conduct closed-door post-mortem with CISO, CHRO, General Counsel, and relevant business leaders -- maintain strict confidentiality due to employment law and potential litigation",
            "Enhance background check programme: implement continuous monitoring (periodic re-screening), expand scope for privileged roles, add financial/credit checks for roles with financial system access",
            "Implement or enhance privilege access management (PAM): deploy just-in-time access, session recording for privileged sessions, automated access recertification every 90 days for sensitive roles",
            "Deploy or tune UEBA with insider threat-specific use cases: after-hours activity, data hoarding, unauthorised data transfer, policy violations, privilege escalation attempts",
            "Update offboarding process: implement automated access revocation across all systems within 1 hour of termination/resignation notification, add exit interview questions about data handling, conduct post-departure access audit at 30 days",
            "Enhance DLP for insider threat scenarios: deploy endpoint DLP with USB blocking, email DLP with personal address detection, cloud DLP for unsanctioned SaaS uploads, printer DLP for sensitive document printing",
            "Conduct insider threat tabletop exercise within 90 days -- test coordination between Security, HR, Legal, and business units; validate that the updated runbook reflects real organisational dynamics",
        ],
        responsible_team="CISO Office / HR / Legal",
        sla_minutes=10080,
        escalation_trigger="Second insider incident within 6 months OR control gap remediation not actioned within agreed timeframe",
    ),
]

INSIDER_TEMPLATE = RunbookTemplate(
    incident_type="insider",
    base_stages=INSIDER_STAGES,
    default_contacts={
        "Incident Commander": {"name": "CISO", "email": "ciso@company.com", "phone": "+1-555-0500"},
        "HR Lead": {"name": "HR Director", "email": "hr-director@company.com", "phone": "+1-555-0501"},
        "Legal Lead": {"name": "Employment Counsel", "email": "employment-legal@company.com", "phone": "+1-555-0502"},
        "Technical Lead": {"name": "CSIRT Lead", "email": "csirt@company.com", "phone": "+1-555-0503"},
        "Physical Security": {"name": "Head of Physical Security", "email": "physical-security@company.com", "phone": "+1-555-0504"},
        "PR/Comms": {"name": "VP Communications", "email": "comms@company.com", "phone": "+1-555-0505"},
    },
    default_tools=[
        {"name": "UEBA Platform (Splunk UBA / Exabeam)", "purpose": "User behaviour analytics -- anomaly detection, peer group analysis, risk scoring"},
        {"name": "DLP Platform", "purpose": "Detect and block unauthorised data exfiltration via email, USB, cloud, and print"},
        {"name": "Okta / Azure AD", "purpose": "Account suspension, session revocation, access log analysis"},
        {"name": "SIEM / Splunk", "purpose": "Cross-system log correlation, timeline reconstruction, alert management"},
        {"name": "PAM Solution (CyberArk / BeyondTrust)", "purpose": "Privileged session monitoring, credential vaulting, just-in-time access"},
        {"name": "HRIS (Workday / SAP SuccessFactors)", "purpose": "Employment status, disciplinary history, role changes, trigger event data"},
    ],
    default_comms=[
        "HR Director and Employment Counsel engaged BEFORE any investigative action is taken -- insider investigations are legally sensitive",
        "Strict need-to-know communication protocol: information shared only with those directly involved in investigation or decision-making",
        "No communication to the individual until authorised by HR and Legal -- premature confrontation can compromise evidence preservation and legal position",
        "Internal communication to affected team managed by HR with approved script addressing business continuity without disclosing investigation details",
        "External communication (media, regulators, customers) managed by Legal and Communications -- do NOT disclose the individual's identity or employment details",
        "Law enforcement engagement decided jointly by CISO, General Counsel, and CEO -- consider impact on regulatory obligations, insurance, and publicity",
    ],
)

# ─────────────────────────────────────────────────────────────────
# Template: Credential Theft
# ─────────────────────────────────────────────────────────────────

CREDENTIAL_STAGES = [
    IRStage(
        stage_number=1,
        stage_name="Identification",
        description="Detect compromised credentials through identity-based alerts and threat intelligence.",
        actions=[
            "Triage impossible travel alerts: user authenticating from two geographically distant locations within an impossible timeframe (e.g., London login then Sydney login 10 minutes later)",
            "Investigate MFA fatigue alerts: multiple MFA push notifications sent and eventually accepted, suspicious MFA method change (SMS to authenticator app swap then immediate login), MFA enrollment from new device followed by unusual activity",
            "Review credential stuffing indicators: high rate of failed login attempts across multiple accounts from same IP, followed by successful logins on a subset -- indicates breached credentials being tested at scale",
            "Check threat intelligence feeds for compromised credentials: credential dumps on dark web (Have I Been Pwned domain monitoring, SpyCloud, Flashpoint) containing corporate email addresses and passwords",
            "Correlate login anomalies with email forwarding rule creation, mailbox delegation changes, and OAuth application consent grants -- these are common post-compromise actions taken by attackers",
            "Declare severity based on privilege level of compromised account: standard user (SEV3), privileged business user / finance / HR (SEV2), domain admin, cloud admin, or C-level (SEV1)",
        ],
        responsible_team="SOC Tier 1 / Identity Security",
        sla_minutes=15,
        escalation_trigger="Compromised account has privileged access (domain admin, cloud admin, finance, HR, executive) OR credential dump contains >50 corporate accounts with valid passwords",
    ),
    IRStage(
        stage_number=2,
        stage_name="Containment",
        description="Lock down compromised accounts and prevent attacker from maintaining access.",
        actions=[
            "Force password reset on the compromised account and all accounts that share the same credentials -- check password manager/SSO for credential reuse patterns",
            "Revoke all active sessions for the compromised account across all applications: IdP session revocation (Okta/Azure AD sign-out everywhere), SaaS application-specific session termination (O365, Salesforce, GitHub, AWS console)",
            "Disable or revoke all API keys, OAuth tokens, personal access tokens, and SSH keys associated with the account -- generate new credentials before re-enabling",
            "Block source IP addresses and ASNs associated with the malicious logins at the perimeter firewall and VPN concentrator",
            "Enforce MFA re-registration for the compromised user: revoke existing MFA methods, require re-enrollment from a known-corporate device, verify identity through manager confirmation before re-enabling",
            "Place the affected account under enhanced monitoring: enable step-up authentication for all access attempts, log all activity at verbose level, alert on any privilege escalation or sensitive data access",
        ],
        responsible_team="CSIRT / Identity Management",
        sla_minutes=30,
        escalation_trigger="Attacker accessed sensitive systems (finance, HR, intellectual property) using compromised credentials OR lateral movement to additional accounts detected",
    ),
    IRStage(
        stage_number=3,
        stage_name="Eradication",
        description="Identify full scope of compromise and eliminate attacker persistence.",
        actions=[
            "Audit all activity performed by the compromised account during the breach window: review IdP sign-in logs, SaaS application audit logs, database query logs, file access logs, and email sent items",
            "Check for persistence mechanisms created by the attacker: email forwarding rules to external addresses, OAuth application consent grants, mailbox delegation permissions, additional MFA methods enrolled, new API keys generated",
            "Review all accounts with shared or similar characteristics: accounts where the user has delegated access, service accounts with same password pattern, privileged accounts the user can manage -- expand investigation to these accounts",
            "Rotate all credentials the compromised account had access to: shared mailbox passwords, service account credentials, database connection strings, CI/CD secrets (GitHub Actions secrets, Jenkins credentials, Ansible vault)",
            "If credentials were obtained via malware on the user's endpoint: follow Malware Outbreak runbook for that specific host to ensure no keylogger or token stealer remains",
            "Validate eradication by reviewing login activity and audit logs for 24 hours after credential rotation -- confirm attacker cannot re-authenticate using any previously compromised credential",
        ],
        responsible_team="CSIRT / Identity Management",
        sla_minutes=120,
        escalation_trigger="Attacker created persistent access mechanisms on multiple systems OR evidence that service account or machine identity also compromised",
    ),
    IRStage(
        stage_number=4,
        stage_name="Recovery",
        description="Restore secure account access and verify no persistence remains.",
        actions=[
            "Re-enable the user's account with new credentials, new MFA enrollment, and mandatory security awareness training on phishing/credential hygiene before access restoration",
            "Restore access to applications and systems in a phased manner: email first, then business applications (CRM, ERP), then development tools (GitHub, CI/CD), then administrative consoles -- verify no anomalous activity at each step",
            "Verify and restore any legitimate email forwarding rules, mailbox delegates, and application integrations that were removed during eradication -- validate each one with the user before re-enabling",
            "Monitor the recovered account with enhanced logging for 30 days: alert on any new MFA enrollment, API key creation, application consent grant, or privilege elevation",
            "Notify affected stakeholders if the compromised account was used to send phishing emails internally, access shared data, or modify business records -- affected parties need to verify data integrity",
            "Conduct targeted phishing simulation for the user's department to assess broader susceptibility to the credential theft vector identified (phishing, credential stuffing, MFA fatigue)",
        ],
        responsible_team="Identity Management / Application Support",
        sla_minutes=180,
        escalation_trigger="Attacker re-authenticates after recovery actions OR evidence that attacker pivoted to other identities during compromise window",
    ),
    IRStage(
        stage_number=5,
        stage_name="Post-Incident Analysis",
        description="Determine how credentials were compromised and assess full scope of impact.",
        actions=[
            "Determine credential compromise vector: phishing (analyse email gateway logs), credential stuffing (check for breached password reuse), MFA fatigue (review MFA push logs), token theft (analyse endpoint for malware), shoulder surfing, password spray from known attacker IPs",
            "If password was found in breach database: compare the compromised password against known credential dumps (Have I Been Pwned, DeHashed) to determine which third-party breach exposed the credential -- assess whether password reuse across personal and corporate accounts was the root cause",
            "Reconstruct full timeline of attacker activity: initial login, privilege escalation attempts, lateral movement, data accessed, persistence mechanisms created, outbound communication to C2 -- map to MITRE ATT&CK (T1078 Valid Accounts, T1110 Brute Force, T1621 MFA Request Generation)",
            "Assess data exposure: enumerate every record, file, email, and system the compromised account accessed during the breach window -- classify by sensitivity and determine regulatory notification obligations",
            "Calculate incident metrics: time from credential compromise to initial login (may be indeterminate if offline theft), time from login to detection, systems accessed, data exposure classification, accounts affected in lateral movement",
            "Produce post-incident report with credential compromise root cause, attacker activity timeline, data exposure assessment, and recommendations for identity security improvement",
        ],
        responsible_team="CSIRT / Identity Security / Threat Intelligence",
        sla_minutes=360,
        escalation_trigger="Compromise sourced from third-party breach affecting the organisation directly (not just user password reuse) OR attacker accessed regulatory-scoped data",
    ),
    IRStage(
        stage_number=6,
        stage_name="Lessons Learned & Closure",
        description="Strengthen identity security posture and reduce credential theft risk.",
        actions=[
            "Conduct post-mortem focused on identity security controls: MFA coverage gaps, password policy effectiveness, credential theft detection capability, session management weaknesses, and identity threat detection maturity",
            "Enforce MFA for ALL users across ALL access methods: eliminate MFA exclusion groups, deploy phishing-resistant MFA (FIDO2/WebAuthn security keys) for privileged roles, implement conditional access policies requiring MFA for all external access",
            "Deploy passwordless authentication where possible: Windows Hello for Business, Passkeys, certificate-based authentication -- reduce the attack surface of phishable credentials entirely",
            "Implement breached password detection: integrate Have I Been Pwned API with password change flow and continuous credential monitoring (Azure AD Password Protection, Okta Passworld, Enzoic)",
            "Enhance identity threat detection: deploy identity-specific detection rules in SIEM (impossible travel, MFA fatigue, suspicious inbox rules, token replay, pass-the-cookie), integrate UEBA risk scoring into conditional access policies",
            "Conduct identity security assessment: review password policy (minimum 14 characters, no complexity rotation), service account management (no interactive login, managed identities), API key lifecycle (automated rotation every 90 days), and privileged access review cadence",
            "Roll out security awareness training focused on credential hygiene: password managers, recognising phishing/MFA fatigue attacks, never reusing corporate passwords on third-party sites, reporting suspicious MFA prompts immediately",
        ],
        responsible_team="CISO Office / Identity Security / Security Awareness",
        sla_minutes=7200,
        escalation_trigger="Repeat credential theft incident within 90 days OR identity security assessment reveals systemic MFA gaps across critical systems",
    ),
]

CREDENTIAL_TEMPLATE = RunbookTemplate(
    incident_type="credential",
    base_stages=CREDENTIAL_STAGES,
    default_contacts={
        "Incident Commander": {"name": "Identity Security Lead", "email": "identity-sec@company.com", "phone": "+1-555-0600"},
        "Technical Lead": {"name": "CSIRT Engineer", "email": "csirt@company.com", "phone": "+1-555-0601"},
        "IAM Engineering": {"name": "IAM Team Lead", "email": "iam@company.com", "phone": "+1-555-0602"},
        "Communications": {"name": "CISO Office", "email": "ciso-office@company.com", "phone": "+1-555-0603"},
        "Legal": {"name": "General Counsel", "email": "legal@company.com", "phone": "+1-555-0604"},
        "User's Manager": {"name": "Department Head", "email": "dept-head@company.com", "phone": "+1-555-0605"},
    },
    default_tools=[
        {"name": "Okta / Azure AD / IdP", "purpose": "Identity provider -- session revocation, MFA enforcement, sign-in log analysis, conditional access"},
        {"name": "Splunk / SIEM", "purpose": "Login anomaly detection, impossible travel alerting, cross-system correlation"},
        {"name": "Have I Been Pwned / SpyCloud", "purpose": "Breached password and credential dump monitoring"},
        {"name": "PAM Solution (CyberArk / Delinea)", "purpose": "Privileged account session management and credential rotation"},
        {"name": "Email Security Gateway (Mimecast / Proofpoint)", "purpose": "Phishing detection and mailbox rule monitoring"},
        {"name": "PagerDuty", "purpose": "Incident alerting and team mobilisation"},
    ],
    default_comms=[
        "Identity Security Lead declares incident and mobilises CSIRT and IAM teams via PagerDuty",
        "Affected user's manager notified (but NOT the user directly until investigation confirms compromise)",
        "Internal communication to IT Service Desk with guidance on handling user reports of account lockout or MFA issues related to the incident",
        "Broader user communication if the credential theft vector (e.g., phishing campaign) affects multiple users -- send awareness alert with specific indicators to look for",
        "All-clear communication when account is secured and access restored, with guidance on new security measures implemented",
    ],
)

# ─────────────────────────────────────────────────────────────────
# Template registry
# ─────────────────────────────────────────────────────────────────

TEMPLATES: dict[str, RunbookTemplate] = {
    "malware": MALWARE_TEMPLATE,
    "ransomware": RANSOMWARE_TEMPLATE,
    "breach": BREACH_TEMPLATE,
    "ddos": DDOS_TEMPLATE,
    "insider": INSIDER_TEMPLATE,
    "credential": CREDENTIAL_TEMPLATE,
}

TEMPLATE_LIST: list[str] = list(TEMPLATES.keys())

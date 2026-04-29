"""Demo organisation context -- PayFlow Ltd, a realistic fintech company."""


def get_demo_context() -> dict:
    """Return a realistic demo context for a PCI-DSS regulated fintech.

    PayFlow Ltd processes payments, is PCI-DSS regulated, AWS-hosted,
    and uses CrowdStrike + Splunk + Okta + PagerDuty.
    """
    return {
        "org_name": "PayFlow Ltd",
        "industry": "Financial Technology (FinTech)",
        "regulatory_reqs": ["PCI-DSS", "GDPR", "SOX", "NIS2"],
        "specific_threats": [
            "ransomware targeting financial services",
            "payment card data skimming",
            "credential stuffing against payment APIs",
            "insider threat from privileged payment system administrators",
        ],
        "tool_stack": [
            {"name": "CrowdStrike Falcon", "purpose": "Endpoint detection and response, host isolation, IOC scanning"},
            {"name": "Splunk Enterprise Security", "purpose": "SIEM, log aggregation, correlation searches, timeline reconstruction"},
            {"name": "Okta Workforce Identity", "purpose": "Identity provider, SSO, MFA enforcement, session revocation"},
            {"name": "PagerDuty Enterprise", "purpose": "Incident alerting, on-call escalation, team mobilisation"},
            {"name": "AWS WAF & Shield Advanced", "purpose": "DDoS mitigation, web application firewall, rate limiting"},
            {"name": "Veeam Backup & Replication", "purpose": "Immutable backups, disaster recovery, ransomware protection"},
            {"name": "CyberArk PAM", "purpose": "Privileged access management, session recording, credential vaulting"},
            {"name": "Mimecast Email Security", "purpose": "Email security gateway, phishing protection, mailbox monitoring"},
            {"name": "Forcepoint DLP", "purpose": "Data loss prevention, sensitive data exfiltration detection"},
        ],
        "cloud_provider": "AWS (eu-west-2, eu-west-1 DR)",
        "data_classification": "PCI-DSS Level 1 merchant data, PII (UK/EEA data subjects), SOX-scoped financial data",
    }

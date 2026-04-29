"""Built-in demo questionnaire — ~25 questions across 7 categories.

The demo tells a story: this vendor (CloudMatrix Ltd) has good access controls
and compliance posture, but weak data protection and encryption practices.
"""


def get_demo_questions() -> tuple[str, list[dict]]:
    """Return (vendor_name, list of question dicts ready for CSV parser)."""

    vendor_name = "CloudMatrix Ltd"

    questions = [
        # AccessControl (3 Qs) — Strong, all YES
        {"category": "AccessControl", "question": "Does the vendor enforce MFA for all privileged access?", "weight": "HIGH", "answer": "YES", "notes": "SSO with enforced MFA via Okta"},
        {"category": "AccessControl", "question": "Are access reviews conducted at least quarterly?", "weight": "MEDIUM", "answer": "YES", "notes": ""},
        {"category": "AccessControl", "question": "Is role-based access control (RBAC) implemented across all systems?", "weight": "MEDIUM", "answer": "YES", "notes": ""},

        # DataProtection (4 Qs) — Weak: NO on HIGH-weight items
        {"category": "DataProtection", "question": "Is customer data classified and labelled according to sensitivity?", "weight": "HIGH", "answer": "NO", "notes": "No formal classification scheme in place"},
        {"category": "DataProtection", "question": "Are data retention and deletion policies documented and enforced?", "weight": "HIGH", "answer": "NO", "notes": "Policy exists but not enforced"},
        {"category": "DataProtection", "question": "Does the vendor maintain a data inventory or data flow map?", "weight": "MEDIUM", "answer": "PARTIAL", "notes": "Inventory exists for production only; dev/staging undocumented"},
        {"category": "DataProtection", "question": "Is personal data processing compliant with applicable privacy regulations (GDPR/CCPA)?", "weight": "HIGH", "answer": "YES", "notes": "DPO appointed, GDPR compliance program active"},

        # Encryption (4 Qs) — Weak: NO on HIGH-weight items
        {"category": "Encryption", "question": "Is all customer data encrypted at rest using AES-256 or equivalent?", "weight": "HIGH", "answer": "NO", "notes": "Some legacy volumes use default encryption only"},
        {"category": "Encryption", "question": "Is TLS 1.2+ enforced for all data in transit?", "weight": "HIGH", "answer": "YES", "notes": ""},
        {"category": "Encryption", "question": "Are encryption keys managed via a dedicated KMS/HSM?", "weight": "HIGH", "answer": "NO", "notes": "Keys stored alongside data in some non-production environments"},
        {"category": "Encryption", "question": "Is there a documented key rotation policy with a maximum 90-day rotation window?", "weight": "MEDIUM", "answer": "PARTIAL", "notes": "Policy exists but rotation not automated"},

        # IncidentResponse (4 Qs)
        {"category": "IncidentResponse", "question": "Does the vendor have a documented incident response plan?", "weight": "HIGH", "answer": "YES", "notes": ""},
        {"category": "IncidentResponse", "question": "Are incident response tabletop exercises conducted annually?", "weight": "MEDIUM", "answer": "PARTIAL", "notes": "Last tabletop was 18 months ago"},
        {"category": "IncidentResponse", "question": "Does the vendor maintain 24/7 security monitoring with defined SLAs?", "weight": "HIGH", "answer": "YES", "notes": "SOC 2 Type II certified"},
        {"category": "IncidentResponse", "question": "Is there a documented breach notification process (<72 hours)?", "weight": "MEDIUM", "answer": "YES", "notes": ""},

        # BCP (4 Qs)
        {"category": "BCP", "question": "Is there a documented and tested business continuity plan?", "weight": "HIGH", "answer": "YES", "notes": "Annual BCP test completed"},
        {"category": "BCP", "question": "Are RTO and RPO defined for all critical systems?", "weight": "MEDIUM", "answer": "PARTIAL", "notes": "Defined for production only"},
        {"category": "BCP", "question": "Does the vendor maintain geographically diverse disaster recovery sites?", "weight": "MEDIUM", "answer": "NO", "notes": "Single-region DR currently"},
        {"category": "BCP", "question": "Are backups tested for restore capability at least quarterly?", "weight": "HIGH", "answer": "YES", "notes": ""},

        # SupplierMgmt (3 Qs)
        {"category": "SupplierMgmt", "question": "Does the vendor assess security posture of their own sub-processors?", "weight": "HIGH", "answer": "PARTIAL", "notes": "Assessment performed at onboarding only, no ongoing monitoring"},
        {"category": "SupplierMgmt", "question": "Are sub-processor dependencies disclosed and updated in contract schedules?", "weight": "MEDIUM", "answer": "YES", "notes": ""},
        {"category": "SupplierMgmt", "question": "Does the vendor maintain a supplier risk register?", "weight": "MEDIUM", "answer": "NO", "notes": ""},

        # Compliance (4 Qs) — Strong
        {"category": "Compliance", "question": "Does the vendor hold a current SOC 2 Type II report?", "weight": "HIGH", "answer": "YES", "notes": "Latest report dated Q1 2026"},
        {"category": "Compliance", "question": "Is the vendor ISO 27001 certified?", "weight": "HIGH", "answer": "YES", "notes": "Certificate valid through 2027"},
        {"category": "Compliance", "question": "Are regular penetration tests performed by an independent third party?", "weight": "MEDIUM", "answer": "YES", "notes": "Annual pen test; last: Nov 2025"},
        {"category": "Compliance", "question": "Does the vendor have a documented vulnerability disclosure program?", "weight": "LOW", "answer": "PARTIAL", "notes": "Security.txt exists but no formal bug bounty"},

        # Bonus: N/A case
        {"category": "Compliance", "question": "Is the vendor PCI DSS certified? (if handling cardholder data)", "weight": "LOW", "answer": "NA", "notes": "Vendor does not process payment card data"},
    ]

    return vendor_name, questions

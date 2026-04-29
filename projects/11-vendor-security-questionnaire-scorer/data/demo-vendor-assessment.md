# Vendor Security Assessment: CloudMatrix Ltd

**Date:** 2026-04-29  
**Overall Score:** 68.2%  
**Risk Rating:** **HIGH**  

*27 questions (26 scored, 1 N/A)*

## Category Breakdown

| Category | Score | Max | Pct | Rating |
|----------|------:|----:|----:|--------|
| AccessControl | 7.0 | 7.0 | 100.0% | LOW |
| DataProtection | 4.0 | 11.0 | 36.4% | CRITICAL |
| Encryption | 4.0 | 11.0 | 36.4% | CRITICAL |
| IncidentResponse | 9.0 | 10.0 | 90.0% | LOW |
| BCP | 7.0 | 10.0 | 70.0% | MEDIUM |
| SupplierMgmt | 3.5 | 7.0 | 50.0% | HIGH |
| Compliance | 8.5 | 9.0 | 94.4% | LOW |

## Top Risks

- [DataProtection] Is customer data classified and labelled according to sensitivity?
- [DataProtection] Are data retention and deletion policies documented and enforced?
- [Encryption] Is all customer data encrypted at rest using AES-256 or equivalent?
- [Encryption] Are encryption keys managed via a dedicated KMS/HSM?

## Remediation Checklist

- [DataProtection] Is customer data classified and labelled according to sensitivity? — Vendor response was NO. Require remediation plan with committed timeline before contract signing.
- [DataProtection] Are data retention and deletion policies documented and enforced? — Vendor response was NO. Require remediation plan with committed timeline before contract signing.
- [DataProtection] Does the vendor maintain a data inventory or data flow map? — Vendor response was PARTIAL. Request evidence of partial implementation and gap-closure roadmap.
- [Encryption] Is all customer data encrypted at rest using AES-256 or equivalent? — Vendor response was NO. Require remediation plan with committed timeline before contract signing.
- [Encryption] Are encryption keys managed via a dedicated KMS/HSM? — Vendor response was NO. Require remediation plan with committed timeline before contract signing.
- [Encryption] Is there a documented key rotation policy with a maximum 90-day rotation window? — Vendor response was PARTIAL. Request evidence of partial implementation and gap-closure roadmap.
- [IncidentResponse] Are incident response tabletop exercises conducted annually? — Vendor response was PARTIAL. Request evidence of partial implementation and gap-closure roadmap.
- [BCP] Are RTO and RPO defined for all critical systems? — Vendor response was PARTIAL. Request evidence of partial implementation and gap-closure roadmap.
- [BCP] Does the vendor maintain geographically diverse disaster recovery sites? — Vendor response was NO. Require remediation plan with committed timeline before contract signing.
- [SupplierMgmt] Does the vendor assess security posture of their own sub-processors? — Vendor response was PARTIAL. Request evidence of partial implementation and gap-closure roadmap.
- [SupplierMgmt] Does the vendor maintain a supplier risk register? — Vendor response was NO. Require remediation plan with committed timeline before contract signing.
- [Compliance] Does the vendor have a documented vulnerability disclosure program? — Vendor response was PARTIAL. Request evidence of partial implementation and gap-closure roadmap.

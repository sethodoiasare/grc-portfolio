"""
Seed the Vuln SLA Tracker with realistic dummy data across Nessus, OpenVAS, and Qualys scanners.

Run: python -m src.seed_data
"""

import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.database import init_db, get_db
from src.auth import register_user, hash_password
from src.models import Severity, VulnStatus, ScannerType

# ── Realistic asset pools ──────────────────────────────────────────────────

ASSETS = [
    # (hostname, ip, type)
    ("dc01.vodafone.local", "10.42.1.10", "Domain Controller"),
    ("dc02.vodafone.local", "10.42.1.11", "Domain Controller"),
    ("exch01.vodafone.local", "10.42.2.20", "Exchange Server"),
    ("exch02.vodafone.local", "10.42.2.21", "Exchange Server"),
    ("sql-prod-01.vodafone.local", "10.42.3.10", "SQL Server"),
    ("sql-prod-02.vodafone.local", "10.42.3.11", "SQL Server"),
    ("web-farm-01.vodafone.local", "10.42.4.10", "Web Server"),
    ("web-farm-02.vodafone.local", "10.42.4.11", "Web Server"),
    ("web-farm-03.vodafone.local", "10.42.4.12", "Web Server"),
    ("sap-app-01.vodafone.local", "10.42.5.10", "SAP Application Server"),
    ("sap-db-01.vodafone.local", "10.42.5.20", "SAP HANA DB"),
    ("vcenter-01.vodafone.local", "10.42.6.10", "vCenter"),
    ("esxi-01.vodafone.local", "10.42.6.21", "ESXi Host"),
    ("esxi-02.vodafone.local", "10.42.6.22", "ESXi Host"),
    ("esxi-03.vodafone.local", "10.42.6.23", "ESXi Host"),
    ("filesrv-01.vodafone.local", "10.42.7.10", "File Server"),
    ("print-01.vodafone.local", "10.42.7.20", "Print Server"),
    ("jump-01.vodafone.local", "10.42.8.10", "Jump Box"),
    ("monitor-01.vodafone.local", "10.42.9.10", "Monitoring Server"),
    ("proxy-01.vodafone.local", "10.42.10.10", "Proxy Server"),
]

VULN_TEMPLATES = [
    # (title, description, severity, cvss, cve, port, proto, solution)
    ("Microsoft Windows Remote Code Execution (PrintNightmare)",
     "Windows Print Spooler RCE vulnerability allowing SYSTEM-level code execution.",
     Severity.CRITICAL, 9.8, "CVE-2021-34527", 445, "tcp",
     "Apply KB5005010 or disable the Print Spooler service on domain controllers."),
    ("Apache Log4j2 Remote Code Execution (Log4Shell)",
     "JNDI injection in Log4j2 <=2.14.1 allows unauthenticated RCE via crafted LDAP/JNDI lookup.",
     Severity.CRITICAL, 10.0, "CVE-2021-44228", 8080, "tcp",
     "Upgrade Log4j to 2.17.1+; set log4j2.formatMsgNoLookups=true."),
    ("OpenSSL Heartbleed Information Disclosure",
     "Missing bounds check in TLS heartbeat extension leaks up to 64KB of server memory.",
     Severity.HIGH, 7.5, "CVE-2014-0160", 443, "tcp",
     "Upgrade OpenSSL to 1.0.1g+ or recompile with -DOPENSSL_NO_HEARTBEATS."),
    ("SMBv1 Remote Code Execution (EternalBlue)",
     "SMBv1 mishandles crafted packets, enabling remote code execution and worm propagation.",
     Severity.CRITICAL, 9.3, "CVE-2017-0144", 445, "tcp",
     "Apply MS17-010; disable SMBv1 via Set-SmbServerConfiguration -EnableSMB1Protocol $false."),
    ("VMware vCenter Server File Upload RCE",
     "Arbitrary file upload in vCenter Analytics service allows authenticated RCE.",
     Severity.CRITICAL, 9.8, "CVE-2021-22005", 443, "tcp",
     "Apply VMware VMSA-2021-0020 patch immediately."),
    ("Cisco IOS XE Web UI Privilege Escalation",
     "Unauthenticated attacker can create a privilege 15 account via the web UI.",
     Severity.CRITICAL, 10.0, "CVE-2023-20198", 443, "tcp",
     "Disable HTTP(S) server on internet-facing devices; apply Cisco advisory patch."),
    ("Zyxel Firewall Hardcoded Credentials",
     "Undocumented user account 'zyfwp' with hardcoded password allows SSH/RCE access.",
     Severity.CRITICAL, 9.8, "CVE-2020-29583", 22, "tcp",
     "Patch firmware to ZLD V4.60 Patch 1 or later."),
    ("Microsoft Exchange ProxyNotShell RCE",
     "Chained SSRF and deserialization in Exchange allows authenticated RCE via PowerShell remoting.",
     Severity.HIGH, 8.8, "CVE-2022-41082", 443, "tcp",
     "Apply November 2022 Exchange SU; block known attack patterns at WAF."),
    ("FortiOS SSL-VPN Buffer Overflow",
     "Heap-based buffer overflow in FortiOS SSL-VPN allows unauthenticated RCE.",
     Severity.CRITICAL, 9.6, "CVE-2022-42475", 443, "tcp",
     "Upgrade FortiOS to 7.2.3+/7.0.9+/6.4.11+; verify SSL-VPN configs."),
    ("SAML Token Signature Bypass (Golden SAML)",
     "Misconfigured SAML identity provider allows forged assertions granting arbitrary access.",
     Severity.HIGH, 8.1, "CVE-2021-42279", 443, "tcp",
     "Enforce strict SAML signature validation; rotate AD FS token-signing certificates."),
    ("Follina MSDT Remote Code Execution",
     "Microsoft Support Diagnostic Tool invoked via Word document URI scheme enables RCE.",
     Severity.HIGH, 7.8, "CVE-2022-30190", 0, "tcp",
     "Apply KB5014699; disable MSDT URL protocol via registry key."),
    ("Oracle WebLogic Server Deserialization RCE",
     "T3/IIOP protocol deserialization of untrusted data allows unauthenticated RCE.",
     Severity.CRITICAL, 9.8, "CVE-2020-14882", 7001, "tcp",
     "Apply Oracle October 2020 Critical Patch Update; restrict T3 access."),
    ("Docker Engine Container Escape (runc)",
     "runc race condition allows container breakout to host as root.",
     Severity.HIGH, 7.2, "CVE-2019-5736", 0, "tcp",
     "Upgrade runc to 1.0-rc6+; ensure Docker Engine >= 18.09.2."),
    ("Sudo Heap-Based Buffer Overflow (Baron Samedit)",
     "Heap overflow in sudo pwfeedback enables local unprivileged root escalation.",
     Severity.HIGH, 7.8, "CVE-2021-3156", 0, "tcp",
     "Apply sudo 1.9.5p2+; verify with 'sudoedit -s /' which should return error."),
    ("Kerberos Bronze Bit Attack (CVE-2020-17049)",
     "Kerberos KDC S4U2Self forwardable ticket forgery allows domain privilege escalation.",
     Severity.HIGH, 7.5, "CVE-2020-17049", 88, "tcp",
     "Apply November 2020 Windows security update; enforce PAC validation."),
    ("SSL/TLS Weak Cipher Suites Enabled",
     "Server accepts RC4, 3DES, or export-grade ciphers vulnerable to SWEET32/BEAST attacks.",
     Severity.MEDIUM, 5.9, "", 443, "tcp",
     "Disable RC4, 3DES, and CBC-mode ciphers; enable only TLS 1.2+ AEAD ciphers."),
    ("SNMP Default Community String (public)",
     "SNMP v1/v2c using default 'public' read community string leaks device information.",
     Severity.MEDIUM, 5.3, "", 161, "udp",
     "Disable SNMP v1/v2c; migrate to SNMPv3 with authPriv; replace community strings."),
    ("Self-Signed SSL Certificate",
     "Server using self-signed certificate; vulnerable to MITM impersonation attacks.",
     Severity.LOW, 4.0, "", 443, "tcp",
     "Replace with CA-signed certificate from internal PKI or public trusted CA."),
    ("ICMP Timestamp Request Enabled",
     "Host responds to ICMP timestamp queries leaking system uptime and clock skew.",
     Severity.LOW, 2.6, "", 0, "icmp",
     "Block ICMP type 13/14 at firewall; Linux: echo 1 > /proc/sys/net/ipv4/icmp_echo_ignore_timestamp."),
    ("HTTP TRACE Method Enabled",
     "Web server supports TRACE method, enabling Cross-Site Tracing (XST) attacks.",
     Severity.LOW, 4.3, "", 80, "tcp",
     "Disable TRACE method in web server config; Apache: TraceEnable off."),
    ("TLS 1.0 Protocol Enabled",
     "Server supports TLS 1.0 which is PCI non-compliant and vulnerable to POODLE derivatives.",
     Severity.MEDIUM, 5.0, "", 443, "tcp",
     "Disable TLS 1.0/1.1; enforce TLS 1.2 minimum."),
    ("NFS Export with no_root_squash",
     "NFS share exported without root squashing allows NFS client root to access files as root.",
     Severity.MEDIUM, 6.8, "", 2049, "tcp",
     "Add root_squash to /etc/exports; restrict NFS access to authorised client subnets."),
    ("Weak Password Policy (no complexity)",
     "Domain password policy does not enforce complexity requirements per Vodafone CYBER_014.",
     Severity.MEDIUM, 5.5, "", 0, "tcp",
     "Configure GPO password complexity; minimum 12 chars, 3 of 4 character classes."),
    ("Unpatched Adobe Acrobat Reader",
     "Acrobat Reader version outdated with multiple critical CVEs exploitable via PDF.",
     Severity.HIGH, 7.8, "CVE-2023-21608", 0, "tcp",
     "Deploy Adobe Reader DC Continuous track 23.001.20063+ via SCCM."),
    ("ASP.NET Debug Mode Enabled",
     "ASP.NET application running with debug=true exposes detailed stack traces and configuration.",
     Severity.MEDIUM, 5.3, "", 80, "tcp",
     "Set <compilation debug='false'> in web.config for all production applications."),
]

SERVICES = [("SSH", 22, "tcp"), ("HTTP", 80, "tcp"), ("HTTPS", 443, "tcp"),
            ("MySQL", 3306, "tcp"), ("RDP", 3389, "tcp"), ("SMB", 445, "tcp"),
            ("DNS", 53, "udp"), ("LDAP", 389, "tcp"), ("LDAPS", 636, "tcp"),
            ("WinRM", 5985, "tcp"), ("NFS", 2049, "tcp"), ("PostgreSQL", 5432, "tcp")]


def _random_date(days_ago_min: int = 0, days_ago_max: int = 180) -> str:
    days = random.randint(days_ago_min, days_ago_max)
    dt = datetime.utcnow() - timedelta(days=days)
    return dt.isoformat() + "Z"


def _random_date_between(days_ago_max: int, days_ago_min: int) -> str:
    days = random.randint(days_ago_min, days_ago_max)
    dt = datetime.utcnow() - timedelta(days=days)
    return dt.isoformat() + "Z"


def seed() -> None:
    init_db()
    conn = get_db()
    try:
        # Create demo user
        hashed = hash_password("demo123")
        conn.execute(
            "INSERT OR IGNORE INTO users (email, password_hash, role) VALUES (?, ?, ?)",
            ("demo@vodafone.com", hashed, "auditor"),
        )

        # Create scanner runs
        scanners = [
            ("nessus", "nessus_scan_2026-04-25.csv"),
            ("openvas", "openvas_scan_2026-04-24.csv"),
            ("qualys", "qualys_scan_2026-04-23.csv"),
            ("nessus", "nessus_scan_2026-04-20.csv"),
            ("openvas", "nessus_scan_2026-04-18.csv"),
        ]

        run_ids = []
        for stype, fname in scanners:
            cur = conn.execute(
                "INSERT INTO scanner_runs (scanner_type, filename) VALUES (?, ?)",
                (stype, fname),
            )
            run_ids.append((cur.lastrowid, stype))

        # Generate vulnerabilities
        vuln_count = 0
        for run_id, stype in run_ids:
            num_vulns = random.randint(15, 30)
            shuffled_assets = random.sample(ASSETS, min(len(ASSETS), num_vulns))

            for asset_hostname, asset_ip, asset_type in shuffled_assets:
                template = random.choice(VULN_TEMPLATES)
                title, desc, sev, cvss, cve, port, proto, solution = template

                first_seen = _random_date(days_ago_max=90)
                last_seen = _random_date(days_ago_max=10)

                # 60% open, 25% closed, 10% risk_accepted, 5% false_positive
                status_roll = random.random()
                closed_at = None
                risk_accepted_at = None
                status = VulnStatus.OPEN.value

                if status_roll < 0.25:
                    status = VulnStatus.CLOSED.value
                    closed_at = _random_date_between(
                        max((datetime.utcnow() - datetime.fromisoformat(first_seen.replace("Z", ""))).days - 1, 1),
                        1,
                    )
                elif status_roll < 0.35:
                    status = VulnStatus.RISK_ACCEPTED.value
                    risk_accepted_at = _random_date(days_ago_max=30)
                elif status_roll < 0.40:
                    status = VulnStatus.FALSE_POSITIVE.value

                # Some vulns use service port rather than CVE port
                if port == 0 and random.random() < 0.5:
                    svc = random.choice(SERVICES)
                    port = svc[1]
                    proto = svc[2]

                conn.execute(
                    """INSERT INTO vulnerabilities
                       (scanner_run_id, scanner_type, asset_hostname, asset_ip, title,
                        description, severity, cvss_score, cve_id, port, protocol,
                        solution, status, first_seen, last_seen, closed_at, risk_accepted_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (run_id, stype, asset_hostname, asset_ip, title,
                     desc, sev.value, cvss, cve, port if port else None,
                     proto, solution, status, first_seen, last_seen,
                     closed_at, risk_accepted_at),
                )
                vuln_count += 1

        # Update scanner run counts
        for run_id, stype in run_ids:
            count = conn.execute(
                "SELECT COUNT(*) FROM vulnerabilities WHERE scanner_run_id = ?", (run_id,)
            ).fetchone()[0]
            conn.execute(
                "UPDATE scanner_runs SET vulns_imported = ?, vulns_new = ? WHERE id = ?",
                (count, count, run_id),
            )

        conn.commit()
        print(f"Seeded {vuln_count} vulnerabilities across {len(run_ids)} scanner runs.")
        print(f"Demo user: demo@vodafone.com / demo123")

    finally:
        conn.close()


if __name__ == "__main__":
    seed()

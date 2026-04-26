"""Tests for scanner CSV parsing."""

from src.scanner_parser import parse_scanner_csv, _normalise_severity, _safe_float


NESSUS_CSV = """Host,Host IP,Name,Description,Risk,CVSS,Port,Protocol,Solution,CVE
dc01.vodafone.local,10.42.1.10,MS17-010 EternalBlue,Remote code execution in SMBv1,Critical,9.3,445,tcp,Apply MS17-010,CVE-2017-0144
exch01.vodafone.local,10.42.2.20,ProxyShell RCE,Exchange Server RCE,High,8.8,443,tcp,Apply Exchange SU,CVE-2021-34473
"""

OPENVAS_CSV = """Host,IP,NVT Name,Summary,Severity,CVSS,Port,Protocol,Solution
web-farm-01,10.42.4.10,SSL Weak Ciphers,Weak cipher suites enabled,Medium,5.9,443,tcp,Disable RC4
sql-prod-01,10.42.3.10,SNMP Default Community,Default community string public,Medium,5.3,161,udp,Change community
"""

QUALYS_CSV = """Host,IP,Title,Description,Severity,CVSS,Port,Protocol,Solution,CVE
sap-app-01,10.42.5.10,Log4Shell RCE,Log4j JNDI injection,Critical,10.0,8080,tcp,Upgrade Log4j,CVE-2021-44228
"""


def test_parse_nessus():
    vulns = parse_scanner_csv("nessus", "test.csv", NESSUS_CSV)
    assert len(vulns) == 2
    assert vulns[0].asset_hostname == "dc01.vodafone.local"
    assert vulns[0].cvss_score == 9.3
    assert vulns[0].severity == "Critical"
    assert vulns[0].cve_id == "CVE-2017-0144"
    assert vulns[1].severity == "High"
    assert vulns[1].cve_id == "CVE-2021-34473"


def test_parse_openvas():
    vulns = parse_scanner_csv("openvas", "test.csv", OPENVAS_CSV)
    assert len(vulns) == 2
    assert vulns[0].severity == "Medium"
    assert vulns[0].cvss_score == 5.9
    assert vulns[1].port == 161


def test_parse_qualys():
    vulns = parse_scanner_csv("qualys", "test.csv", QUALYS_CSV)
    assert len(vulns) == 1
    assert vulns[0].title == "Log4Shell RCE"
    assert vulns[0].cvss_score == 10.0
    assert vulns[0].severity == "Critical"
    assert vulns[0].cve_id == "CVE-2021-44228"


def test_parse_empty():
    vulns = parse_scanner_csv("nessus", "empty.csv", "")
    assert len(vulns) == 0


def test_parse_unsupported_scanner():
    try:
        parse_scanner_csv("unknown", "test.csv", "header\n")
        assert False, "Should have raised"
    except ValueError as e:
        assert "Unsupported scanner type" in str(e)


def test_normalise_severity():
    assert _normalise_severity("Critical") == "Critical"
    assert _normalise_severity("CRIT") == "Critical"
    assert _normalise_severity("5") == "Critical"
    assert _normalise_severity("high") == "High"
    assert _normalise_severity("med") == "Medium"
    assert _normalise_severity("low") == "Low"
    assert _normalise_severity("info") == "Info"
    assert _normalise_severity("informational") == "Info"
    assert _normalise_severity("none") == "Info"
    assert _normalise_severity("unknown") == "Unknown"


def test_safe_float():
    assert _safe_float("9.8") == 9.8
    assert _safe_float("0") == 0.0
    assert _safe_float(None) == 0.0
    assert _safe_float("invalid") == 0.0

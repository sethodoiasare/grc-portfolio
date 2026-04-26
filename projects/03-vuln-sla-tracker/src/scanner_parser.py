"""
Parse vulnerability scanner exports into normalised Vulnerability objects.

Supports Nessus CSV, OpenVAS CSV, and Qualys CSV formats.
"""

import csv
import io
from datetime import datetime, timedelta
from typing import Optional

from src.models import Vulnerability, Severity, VulnStatus, ScannerType, severity_from_cvss


def parse_scanner_csv(scanner_type: str, filename: str, content: str) -> list[Vulnerability]:
    """Dispatch to the correct parser based on scanner type."""
    parsers = {
        ScannerType.NESSUS.value: _parse_nessus,
        ScannerType.OPENVAS.value: _parse_openvas,
        ScannerType.QUALYS.value: _parse_qualys,
    }
    parser = parsers.get(scanner_type)
    if parser is None:
        raise ValueError(f"Unsupported scanner type: {scanner_type}")
    return parser(filename, content)


def _parse_nessus(filename: str, content: str) -> list[Vulnerability]:
    """Parse Nessus Professional CSV export."""
    vulns = []
    reader = csv.DictReader(io.StringIO(content))
    for row in reader:
        cvss = _safe_float(row.get("CVSS", row.get("CVSS v3.0 Base Score", "0")))
        severity = row.get("Risk", row.get("Severity", "Info"))
        vuln = Vulnerability(
            scanner_type=ScannerType.NESSUS.value,
            asset_hostname=row.get("Host", row.get("Name", "")),
            asset_ip=row.get("Host IP", ""),
            title=row.get("Name", row.get("Plugin Name", "")),
            description=row.get("Description", ""),
            severity=_normalise_severity(severity),
            cvss_score=cvss,
            cve_id=_extract_cve(row),
            port=_safe_int(row.get("Port")),
            protocol=row.get("Protocol", ""),
            solution=row.get("Solution", ""),
            first_seen=datetime.utcnow().isoformat() + "Z",
            last_seen=datetime.utcnow().isoformat() + "Z",
        )
        if not vuln.severity:
            vuln.severity = severity_from_cvss(cvss).value
        vulns.append(vuln)
    return vulns


def _parse_openvas(filename: str, content: str) -> list[Vulnerability]:
    """Parse OpenVAS / Greenbone CSV export."""
    vulns = []
    reader = csv.DictReader(io.StringIO(content))
    for row in reader:
        cvss = _safe_float(row.get("CVSS", row.get("CVSS Score", "0")))
        vuln = Vulnerability(
            scanner_type=ScannerType.OPENVAS.value,
            asset_hostname=row.get("Host", row.get("Hostname", row.get("IP", ""))),
            asset_ip=row.get("IP", row.get("Host IP", "")),
            title=row.get("NVT Name", row.get("Name", row.get("Vulnerability", ""))),
            description=row.get("Summary", row.get("Description", "")),
            severity=_normalise_severity(row.get("Severity", row.get("Threat", ""))),
            cvss_score=cvss,
            cve_id=_extract_cve(row),
            port=_safe_int(row.get("Port")),
            protocol=row.get("Protocol", ""),
            solution=row.get("Solution", row.get("Solution Type", "")),
            first_seen=datetime.utcnow().isoformat() + "Z",
            last_seen=datetime.utcnow().isoformat() + "Z",
        )
        if not vuln.severity:
            vuln.severity = severity_from_cvss(cvss).value
        vulns.append(vuln)
    return vulns


def _parse_qualys(filename: str, content: str) -> list[Vulnerability]:
    """Parse Qualys Vulnerability Management CSV export."""
    vulns = []
    reader = csv.DictReader(io.StringIO(content))
    for row in reader:
        cvss = _safe_float(row.get("CVSS", row.get("CVSS Score", row.get("CVSS Base", "0"))))
        vuln = Vulnerability(
            scanner_type=ScannerType.QUALYS.value,
            asset_hostname=row.get("Host", row.get("DNS", row.get("Asset", ""))),
            asset_ip=row.get("IP", row.get("IP Address", "")),
            title=row.get("Title", row.get("Vulnerability", row.get("QID Title", ""))),
            description=row.get("Description", row.get("Threat", "")),
            severity=_normalise_severity(row.get("Severity", row.get("Severity Level", ""))),
            cvss_score=cvss,
            cve_id=_extract_cve(row),
            port=_safe_int(row.get("Port")),
            protocol=row.get("Protocol", ""),
            solution=row.get("Solution", row.get("Patch", "")),
            first_seen=datetime.utcnow().isoformat() + "Z",
            last_seen=datetime.utcnow().isoformat() + "Z",
        )
        if not vuln.severity:
            vuln.severity = severity_from_cvss(cvss).value
        vulns.append(vuln)
    return vulns


def _normalise_severity(raw: str) -> str:
    """Map common severity labels to Critical/High/Medium/Low/Info."""
    s = raw.strip().lower()
    mapping = {
        "critical": "Critical", "crit": "Critical", "5": "Critical",
        "high": "High", "4": "High",
        "medium": "Medium", "med": "Medium", "3": "Medium",
        "low": "Low", "2": "Low",
        "info": "Info", "informational": "Info", "none": "Info", "1": "Info", "0": "Info",
    }
    return mapping.get(s, raw.strip().title())


def _safe_float(val: str | None) -> float:
    try:
        return float(val) if val else 0.0
    except (ValueError, TypeError):
        return 0.0


def _safe_int(val: str | None) -> Optional[int]:
    try:
        return int(val) if val else None
    except (ValueError, TypeError):
        return None


def _extract_cve(row: dict) -> str:
    """Pull CVE ID from common column names."""
    for key in ("CVE", "CVEs", "CVE ID", "cve_id", "CVE List", "xref"):
        val = row.get(key, "")
        if val and val.strip():
            cves = []
            for part in val.replace(";", ",").replace("\n", ",").split(","):
                part = part.strip().upper()
                if part.startswith("CVE-"):
                    cves.append(part)
            if cves:
                return cves[0]
    return ""

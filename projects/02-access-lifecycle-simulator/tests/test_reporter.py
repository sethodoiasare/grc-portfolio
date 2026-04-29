"""Tests for reporter module: JSON + PDF export."""

import tempfile
from pathlib import Path
from datetime import datetime, timezone

from src.models import (
    AuditReport, Violation, Severity, ViolationType, SEVERITY_SLA,
)
from src.reporter import (
    export_json, export_pdf, build_audit_report,
    format_summary, generate_access_certification,
)


def _demo_report(violations=None):
    """Build an AuditReport with optional violation list."""
    return AuditReport(
        audit_date=datetime.now(timezone.utc).isoformat(),
        scope="50 AD accounts, 48 HR records, 30 ITSM tickets reviewed",
        summary=format_summary(violations or []),
        violations=violations or [],
        access_certification_items=generate_access_certification(violations or []),
    )


def _make_violation(vid, vtype, sev, desc="Test violation"):
    """Create a single Violation for testing."""
    return Violation(
        violation_id=vid,
        type=vtype,
        severity=sev,
        description=desc,
        affected_accounts=["user.test"],
        control_mapping={"control_id": "IAC-01/D", "control": "Removal of access rights"},
        remediation="Disable the account immediately.",
    )


class TestExportPdf:
    def test_export_pdf_creates_file(self):
        violations = [
            _make_violation("V-001", ViolationType.LEAVER_ACTIVE, Severity.CRITICAL,
                            "Leaver account still enabled"),
            _make_violation("V-002", ViolationType.ORPHANED, Severity.HIGH,
                            "AD account with no HR record"),
            _make_violation("V-003", ViolationType.MFA_MISSING, Severity.HIGH,
                            "Privileged user missing MFA"),
            _make_violation("V-004", ViolationType.SELF_APPROVAL, Severity.HIGH,
                            "Self-approved ITSM ticket"),
        ]
        report = _demo_report(violations)

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test-report.pdf"
            result = export_pdf(report, path)
            assert result == path
            assert path.exists()
            assert path.stat().st_size > 0

    def test_export_pdf_handles_empty_violations(self):
        report = _demo_report([])

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "empty-report.pdf"
            result = export_pdf(report, path)
            assert result == path
            assert path.exists()
            assert path.stat().st_size > 0

    def test_export_pdf_includes_certification_when_present(self):
        violations = [
            _make_violation("V-001", ViolationType.LEAVER_ACTIVE, Severity.CRITICAL),
        ]
        report = _demo_report(violations)
        assert len(report.access_certification_items) > 0

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "cert-report.pdf"
            export_pdf(report, path)
            assert path.stat().st_size > 0


class TestExportJson:
    def test_export_json_writes_valid_output(self):
        violations = [
            _make_violation("V-001", ViolationType.LEAVER_ACTIVE, Severity.CRITICAL),
        ]
        report = _demo_report(violations)

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test-report.json"
            result = export_json(report, path)
            assert result == path
            assert path.exists()
            content = path.read_text()
            assert "V-001" in content
            assert "LEAVER_ACTIVE" in content


class TestHelperFunctions:
    def test_generate_access_certification_assigns_actions(self):
        violations = [
            _make_violation("V-001", ViolationType.LEAVER_ACTIVE, Severity.CRITICAL),
            _make_violation("V-002", ViolationType.MFA_MISSING, Severity.HIGH),
        ]
        items = generate_access_certification(violations)
        assert len(items) == 2
        assert items[0]["action"] == "REVOKE"
        assert items[1]["action"] == "REVIEW"

    def test_format_summary_counts_correctly(self):
        violations = [
            _make_violation("V-001", ViolationType.LEAVER_ACTIVE, Severity.CRITICAL),
            _make_violation("V-002", ViolationType.ORPHANED, Severity.HIGH),
            _make_violation("V-003", ViolationType.MFA_MISSING, Severity.MEDIUM),
        ]
        s = format_summary(violations)
        assert s["total"] == 3
        assert s["by_severity"]["CRITICAL"] == 1
        assert s["by_severity"]["HIGH"] == 1
        assert s["by_severity"]["MEDIUM"] == 1
        assert s["by_type"]["LEAVER_ACTIVE"] == 1

    def test_build_audit_report_has_all_sections(self):
        violations = [
            _make_violation("V-001", ViolationType.LEAVER_ACTIVE, Severity.CRITICAL),
        ]
        report = build_audit_report(violations, ad_count=10, hr_count=8, itsm_count=5)
        assert report.scope == "10 AD accounts, 8 HR records, 5 ITSM tickets reviewed"
        assert report.summary["total"] == 1
        assert len(report.violations) == 1
        assert len(report.access_certification_items) == 1

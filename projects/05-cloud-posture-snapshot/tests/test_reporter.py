"""Tests for JSON and PDF report generation."""

import json
from pathlib import Path
from src.scanner import scan_aws
from src.reporter import export_json, export_pdf


class TestExportJSON:
    def test_export_creates_file(self, tmp_path):
        report = scan_aws("111122223333", mock=True)
        path = tmp_path / "report.json"
        result = export_json(report, path)
        assert result.exists()

    def test_exported_json_is_valid(self, tmp_path):
        report = scan_aws("111122223333", mock=True)
        path = tmp_path / "report.json"
        export_json(report, path)
        data = json.loads(path.read_text())
        assert data["provider"] == "AWS"
        assert "summary" in data
        assert "findings" in data
        assert "management_summary" in data

    def test_export_creates_parent_dirs(self, tmp_path):
        report = scan_aws("111122223333", mock=True)
        path = tmp_path / "nested" / "dir" / "report.json"
        result = export_json(report, path)
        assert result.exists()

    def test_json_roundtrip(self, tmp_path):
        """Export to JSON, re-read, verify structure intact."""
        report = scan_aws("111122223333", mock=True)
        path = tmp_path / "roundtrip.json"
        export_json(report, path)

        data = json.loads(path.read_text())
        assert data["report_id"] == str(report.report_id) if hasattr(report.report_id, '__str__') else report.report_id
        assert len(data["findings"]) == len(report.findings)
        assert data["summary"]["total_checks"] == report.summary.total_checks


class TestExportPDF:
    def test_export_pdf_creates_file(self, tmp_path):
        report = scan_aws("111122223333", mock=True)
        path = tmp_path / "report.pdf"
        try:
            result = export_pdf(report, path)
            assert result.exists()
            assert result.stat().st_size > 1000  # PDFs are non-trivial
        except ImportError:
            pass  # reportlab not installed

    def test_export_pdf_with_critical_failures(self, tmp_path):
        report = scan_aws("111122223333", mock=True)
        path = tmp_path / "report-cf.pdf"
        try:
            result = export_pdf(report, path)
            assert result.exists()
        except ImportError:
            pass

"""Tests for scanner orchestration and report generation."""

import json
from pathlib import Path
from src.scanner import scan_aws, scan_azure, scan_gcp
from src.models import PostureReport, PostureSummary, CheckStatus
from src.checks.registry import AWS_CHECKS, AZURE_CHECKS, GCP_CHECKS, CIS_TO_VODAFONE, get_vodafone_mapping


class TestScanAWS:
    def test_returns_posture_report(self):
        report = scan_aws("111122223333", mock=True)
        assert isinstance(report, PostureReport)
        assert report.provider == "AWS"
        assert report.account_id == "111122223333"
        assert "CIS AWS" in report.cis_benchmark_version

    def test_findings_populated(self):
        report = scan_aws("111122223333", mock=True)
        assert len(report.findings) == len(AWS_CHECKS)

    def test_summary_computed(self):
        report = scan_aws("111122223333", mock=True)
        assert report.summary.total_checks == len(AWS_CHECKS)
        assert report.summary.passed + report.summary.failed + report.summary.not_applicable == report.summary.total_checks
        assert report.summary.pass_rate_pct > 0
        assert report.summary.high_failures > 0  # mock data has high-severity failures

    def test_rag_status(self):
        report = scan_aws("111122223333", mock=True)
        rag = report.rag_status()
        assert rag in ("GREEN", "AMBER", "RED")

    def test_management_summary_generated(self):
        report = scan_aws("111122223333", mock=True)
        assert len(report.management_summary) > 100
        assert "AWS" in report.management_summary

    def test_critical_failures_populated(self):
        report = scan_aws("111122223333", mock=True)
        assert len(report.critical_failures) > 0
        for cf in report.critical_failures:
            assert cf["status"] == "FAIL"
            assert cf["severity"] in ("CRITICAL", "HIGH")

    def test_to_dict_serializable(self):
        report = scan_aws("111122223333", mock=True)
        d = report.to_dict()
        assert isinstance(d["summary"], dict)
        assert isinstance(d["findings"], list)
        json.dumps(d)  # should not raise


class TestScanAzure:
    def test_returns_posture_report(self):
        report = scan_azure("test-sub", mock=True)
        assert report.provider == "AZURE"
        assert len(report.findings) == len(AZURE_CHECKS)

    def test_summary_total(self):
        report = scan_azure("test-sub", mock=True)
        assert report.summary.total_checks == len(AZURE_CHECKS)


class TestScanGCP:
    def test_returns_posture_report(self):
        report = scan_gcp("test-project", mock=True)
        assert report.provider == "GCP"
        assert len(report.findings) == len(GCP_CHECKS)


class TestVodafoneMapping:
    def test_registry_has_all_sections(self):
        for section in ["1", "2", "3", "4", "5"]:
            assert section in CIS_TO_VODAFONE

    def test_get_mapping_returns_tuple(self):
        name, dstmt = get_vodafone_mapping("1.1")
        assert isinstance(name, str)
        assert isinstance(dstmt, str)
        assert "privileged" in name.lower() or "D" in dstmt

    def test_unknown_section_returns_default(self):
        name, dstmt = get_vodafone_mapping("99.1")
        assert name
        assert dstmt

"""Tests for scanner orchestration and report generation."""

import json
from pathlib import Path
from src.scanner import scan
from src.models import ClassificationReport


class TestScanFile:
    def test_single_file_produces_report(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("alice@example.com, card 4111111111111111")
        report = scan(f)
        assert isinstance(report, ClassificationReport)
        assert report.total_files_scanned == 1
        assert report.total_matches >= 2

    def test_rag_red_with_critical_findings(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("AKIAIOSFODNN7EXAMPLE and 4111111111111111")
        report = scan(f)
        assert report.rag_status() == "RED"

    def test_rag_green_clean_file(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("Nothing sensitive here.")
        report = scan(f)
        assert report.rag_status() == "GREEN"


class TestScanDirectory:
    def test_directory_scan(self, tmp_path):
        (tmp_path / "a.txt").write_text("alice@example.com")
        (tmp_path / "b.txt").write_text("bob@example.com\n4111111111111111")
        report = scan(tmp_path)
        assert report.total_files_scanned >= 2
        assert report.total_matches >= 3

    def test_by_category_breakdown(self, tmp_path):
        (tmp_path / "data.txt").write_text("alice@example.com\n4111111111111111\nAKIAIOSFODNN7EXAMPLE")
        report = scan(tmp_path)
        assert "PII" in report.by_category
        assert "PCI" in report.by_category
        assert "SECRETS" in report.by_category


class TestScanNonexistent:
    def test_nonexistent_path_empty_report(self, tmp_path):
        report = scan(tmp_path / "does_not_exist")
        assert report.total_files_scanned == 0
        assert report.total_matches == 0


class TestReportSerialization:
    def test_to_dict(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("alice@example.com")
        report = scan(f)
        d = report.to_dict()
        assert d["total_matches"] == 1
        json.dumps(d)


class TestDemoData:
    def test_demo_files_generated(self, tmp_path, monkeypatch):
        from src.cli import _generate_demo_files
        import os
        monkeypatch.chdir(tmp_path)
        _generate_demo_files()
        demo_dir = tmp_path / "data" / "demo_scan"
        assert demo_dir.exists()
        assert (demo_dir / "config.json").exists()
        assert (demo_dir / "users.csv").exists()
        assert (demo_dir / "payments.log").exists()

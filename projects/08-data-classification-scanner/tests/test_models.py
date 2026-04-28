"""Tests for domain models."""

from src.models import (
    ClassificationMatch, FileScanResult, ClassificationReport,
    DataCategory, Severity, CLASSIFICATION_RULES,
)


class TestClassificationRules:
    def test_all_14_rules_defined(self):
        assert len(CLASSIFICATION_RULES) == 14

    def test_rules_have_required_fields(self):
        for r in CLASSIFICATION_RULES:
            assert r["id"]
            assert r["title"]
            assert r["category"] in DataCategory
            assert r["severity"] in Severity
            assert r["pattern"]
            assert r["description"]

    def test_categories_coverage(self):
        cats = {r["category"] for r in CLASSIFICATION_RULES}
        assert DataCategory.PII in cats
        assert DataCategory.PCI in cats
        assert DataCategory.PHI in cats
        assert DataCategory.SECRETS in cats

    def test_critical_rules_exist(self):
        crit = [r for r in CLASSIFICATION_RULES if r["severity"] == Severity.CRITICAL]
        assert len(crit) >= 6  # PCI + secrets rules

    def test_patterns_compile(self):
        import re
        for r in CLASSIFICATION_RULES:
            re.compile(r["pattern"])


class TestClassificationMatch:
    def test_to_dict(self):
        m = ClassificationMatch(
            rule_id="PII-001", rule_title="Email", category=DataCategory.PII,
            severity=Severity.MEDIUM, match_text="a@b.com",
            file_path="/tmp/test.txt", line_number=5, context="Email: a@b.com",
        )
        d = m.to_dict()
        assert d["category"] == "PII"
        assert d["severity"] == "MEDIUM"


class TestFileScanResult:
    def test_to_dict(self):
        m = ClassificationMatch("PII-001", "Email", DataCategory.PII, Severity.MEDIUM,
                               "a@b.com", "/tmp/t.txt", 1)
        r = FileScanResult("/tmp/t.txt", 100, [m])
        d = r.to_dict()
        assert d["match_count"] == 1
        assert d["critical_count"] == 0

    def test_critical_count(self):
        m1 = ClassificationMatch("PCI-001", "CC", DataCategory.PCI, Severity.CRITICAL,
                                "4111111111111111", "/tmp/t.txt", 1)
        m2 = ClassificationMatch("PII-001", "Email", DataCategory.PII, Severity.MEDIUM,
                                "a@b.com", "/tmp/t.txt", 2)
        r = FileScanResult("/tmp/t.txt", 100, [m1, m2])
        assert r.critical_count() == 1


class TestClassificationReport:
    def test_to_dict(self):
        report = ClassificationReport(
            report_id="r1", generated_at="2026-04-28", scan_root="/tmp",
            total_files_scanned=5, total_matches=10, files_with_findings=3,
            critical_findings=2, high_findings=1, medium_findings=5, low_findings=2,
            by_category={"PII": 6, "PCI": 2, "SECRETS": 2},
        )
        d = report.to_dict()
        assert d["rag_status"] == "RED"

    def test_rag_green(self):
        report = ClassificationReport("r1", "2026", "/tmp", 10, 0, 0, 0, 0, 0, 0)
        assert report.rag_status() == "GREEN"

    def test_rag_amber(self):
        report = ClassificationReport("r1", "2026", "/tmp", 10, 10, 5, 0, 6, 2, 2)
        assert report.rag_status() == "AMBER"

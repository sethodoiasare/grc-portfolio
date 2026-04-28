"""Tests for classification engine."""

from pathlib import Path
from src.classifier import scan_file, scan_directory
from src.models import DataCategory, Severity


class TestScanFile:
    def test_detect_email(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("Contact: alice@example.com for support")
        matches = scan_file(f)
        emails = [m for m in matches if m.rule_id == "PII-001"]
        assert len(emails) == 1
        assert emails[0].match_text == "alice@example.com"
        assert emails[0].category == DataCategory.PII

    def test_detect_credit_card(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("Payment with card 4111111111111111 processed")
        matches = scan_file(f)
        cards = [m for m in matches if m.rule_id == "PCI-001"]
        assert len(cards) == 1
        assert cards[0].severity == Severity.CRITICAL

    def test_detect_aws_key(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("AWS key: AKIAIOSFODNN7EXAMPLE used in prod")
        matches = scan_file(f)
        keys = [m for m in matches if m.rule_id == "SEC-001"]
        assert len(keys) == 1
        assert "AKIA" in keys[0].match_text

    def test_detect_private_key_header(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("-----BEGIN RSA PRIVATE KEY-----\nMIIEpA...\n-----END RSA PRIVATE KEY-----")
        matches = scan_file(f)
        pk = [m for m in matches if m.rule_id == "SEC-003"]
        assert len(pk) == 1

    def test_detect_connection_string(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("mongodb://admin:secretpass@db.internal:27017/production")
        matches = scan_file(f)
        cs = [m for m in matches if m.rule_id == "SEC-005"]
        assert len(cs) == 1

    def test_uk_phone(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("Call +447911123456 for enquiries")
        matches = scan_file(f)
        phones = [m for m in matches if m.rule_id == "PII-004"]
        assert len(phones) == 1

    def test_ssn_format(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("SSN: 123-45-6789 on file")
        matches = scan_file(f)
        ssns = [m for m in matches if m.rule_id == "PII-003"]
        assert len(ssns) == 1

    def test_multiple_matches_in_file(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("Email: a@b.com, Card: 4111111111111111, Key: AKIAIOSFODNN7EXAMPLE")
        matches = scan_file(f)
        assert len(matches) >= 3

    def test_no_matches_clean_file(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("This file contains nothing sensitive.")
        matches = scan_file(f)
        assert len(matches) == 0

    def test_cvv_requires_context_keyword(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("Just a number 1234 here")
        matches = scan_file(f)
        cvvs = [m for m in matches if m.rule_id == "PCI-002"]
        assert len(cvvs) == 0

    def test_cvv_with_context_detected(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("CVV code: 123 on back of card")
        matches = scan_file(f)
        cvvs = [m for m in matches if m.rule_id == "PCI-002"]
        assert len(cvvs) == 1

    def test_binary_file_skipped(self, tmp_path):
        f = tmp_path / "image.png"
        f.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
        matches = scan_file(f)
        assert len(matches) == 0


class TestScanDirectory:
    def test_scans_all_text_files(self, tmp_path):
        (tmp_path / "a.txt").write_text("alice@example.com")
        (tmp_path / "b.txt").write_text("4111111111111111")
        (tmp_path / "sub").mkdir()
        (tmp_path / "sub" / "c.txt").write_text("AKIAIOSFODNN7EXAMPLE")
        matches = scan_directory(tmp_path)
        assert len(matches) == 3

    def test_respects_extension_filter(self, tmp_path):
        (tmp_path / "data.txt").write_text("alice@example.com")
        (tmp_path / "script.py").write_text("bob@example.com")
        matches = scan_directory(tmp_path, extensions=[".py"])
        assert len(matches) == 1
        assert matches[0].match_text == "bob@example.com"

    def test_skips_binary_files(self, tmp_path):
        (tmp_path / "notes.txt").write_text("alice@example.com")
        (tmp_path / "photo.png").write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
        matches = scan_directory(tmp_path)
        assert len(matches) == 1

    def test_skips_hidden_files(self, tmp_path):
        (tmp_path / ".secret.txt").write_text("alice@example.com")
        matches = scan_directory(tmp_path)
        assert len(matches) == 0

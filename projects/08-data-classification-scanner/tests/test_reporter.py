"""Tests for JSON reporter."""

import json
from pathlib import Path
from src.scanner import scan
from src.reporter import export_json


def test_export_json_creates_file(tmp_path):
    f = tmp_path / "test.txt"
    f.write_text("alice@example.com")
    report = scan(f)
    out = tmp_path / "report.json"
    result = export_json(report, out)
    assert result.exists()
    data = json.loads(result.read_text())
    assert data["total_matches"] == 1
    assert data["total_files_scanned"] == 1

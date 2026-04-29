"""Tests for CLI demo mode."""

import json
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent


def test_demo_runs_and_produces_output(tmp_path):
    """The demo command should run without error and produce valid JSON output."""
    output = tmp_path / "demo-report.json"
    result = subprocess.run(
        [sys.executable, "-m", "src.cli", "scan", "--demo", "--output", str(output)],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"stderr: {result.stderr}\nstdout: {result.stdout}"
    assert output.exists()

    data = json.loads(output.read_text())
    assert isinstance(data, list)
    assert len(data) == 4  # All four frameworks

    for entry in data:
        assert "framework" in entry
        assert "total_controls" in entry
        assert "covered" in entry
        assert "partial" in entry
        assert "gap" in entry
        assert "coverage_pct" in entry
        assert entry["total_controls"] == entry["covered"] + entry["partial"] + entry["gap"]


def test_demo_output_contains_actionable_gaps(tmp_path):
    """The demo should produce at least some gaps — otherwise the demo policy is too complete."""
    output = tmp_path / "demo-report.json"
    result = subprocess.run(
        [sys.executable, "-m", "src.cli", "scan", "--demo", "--output", str(output)],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0

    data = json.loads(output.read_text())
    total_gaps = sum(entry["gap"] for entry in data)
    # The demo policy covers many areas but should have some gaps
    assert total_gaps > 0, "Demo policy should produce at least some gaps for the report"


def test_list_frameworks():
    """List-frameworks command should work."""
    result = subprocess.run(
        [sys.executable, "-m", "src.cli", "list-frameworks"],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "ISO27001" in result.stdout
    assert "NIST_CSF" in result.stdout
    assert "CIS_V8" in result.stdout
    assert "VODAFONE" in result.stdout


def test_scan_requires_file_or_demo():
    """Scan without --file or --demo should error."""
    result = subprocess.run(
        [sys.executable, "-m", "src.cli", "scan"],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0


def test_demo_csv_format(tmp_path):
    """The demo command with --format csv should produce only CSV output."""
    output = tmp_path / "demo-report.json"
    result = subprocess.run(
        [sys.executable, "-m", "src.cli", "scan", "--demo", "--output", str(output),
         "--format", "csv"],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"stderr: {result.stderr}\nstdout: {result.stdout}"

    csv_output = tmp_path / "demo-report.csv"
    assert csv_output.exists()
    content = csv_output.read_text()
    assert "Framework" in content
    assert "Control ID" in content


def test_demo_pdf_format(tmp_path):
    """The demo command with --format pdf should produce a valid PDF file."""
    output = tmp_path / "demo-report.json"
    result = subprocess.run(
        [sys.executable, "-m", "src.cli", "scan", "--demo", "--output", str(output),
         "--format", "pdf"],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"stderr: {result.stderr}\nstdout: {result.stdout}"

    pdf_output = tmp_path / "demo-report.pdf"
    assert pdf_output.exists()
    # Basic PDF magic number check
    header = pdf_output.read_bytes()[:5]
    assert header == b"%PDF-", f"Expected PDF header, got: {header!r}"


def test_demo_all_formats(tmp_path):
    """The demo command with --format all should produce JSON, CSV, and PDF."""
    output = tmp_path / "demo-report.json"
    result = subprocess.run(
        [sys.executable, "-m", "src.cli", "scan", "--demo", "--output", str(output),
         "--format", "all"],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"stderr: {result.stderr}\nstdout: {result.stdout}"

    assert output.exists()  # JSON
    assert (tmp_path / "demo-report.csv").exists()
    pdf_out = tmp_path / "demo-report.pdf"
    assert pdf_out.exists()
    assert pdf_out.read_bytes()[:5] == b"%PDF-"

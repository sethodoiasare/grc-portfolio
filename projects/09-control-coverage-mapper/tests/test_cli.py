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

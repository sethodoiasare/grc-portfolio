"""Tests for CLI demo mode."""

import subprocess
import sys
from pathlib import Path


def test_demo_runs_and_produces_output():
    project_dir = Path(__file__).resolve().parent.parent
    result = subprocess.run(
        [sys.executable, "-m", "src.cli", "score", "--demo"],
        cwd=str(project_dir),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"CLI stderr:\n{result.stderr}"
    stdout = result.stdout
    assert "VENDOR SECURITY ASSESSMENT" in stdout
    assert "CloudMatrix Ltd" in stdout
    assert "Risk Rating" in stdout
    assert "CATEGORY BREAKDOWN" in stdout
    assert "TOP RISKS" in stdout
    assert "REMEDIATION CHECKLIST" in stdout


def test_demo_generates_json_output(tmp_path):
    project_dir = Path(__file__).resolve().parent.parent
    out = tmp_path / "test-output.json"
    result = subprocess.run(
        [sys.executable, "-m", "src.cli", "score", "--demo", "--output", str(out)],
        cwd=str(project_dir),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    import json
    data = json.loads(out.read_text())
    assert data["vendor_name"] == "CloudMatrix Ltd"
    assert "overall_score" in data
    assert "risk_rating" in data
    assert len(data["category_scores"]) == 7
    assert len(data["top_risks"]) > 0
    assert len(data["remediation_checklist"]) > 0


def test_demo_generates_pdf_output(tmp_path):
    project_dir = Path(__file__).resolve().parent.parent
    out = tmp_path / "test-output.pdf"
    result = subprocess.run(
        [sys.executable, "-m", "src.cli", "score", "--demo", "--output", str(out), "--format", "pdf"],
        cwd=str(project_dir),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"CLI stderr:\n{result.stderr}"
    assert out.exists()
    assert out.stat().st_size > 1000  # PDF should be non-trivial
    content = out.read_bytes()
    assert content.startswith(b"%PDF-")

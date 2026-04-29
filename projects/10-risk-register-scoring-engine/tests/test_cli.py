"""Tests for CLI."""

import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

from src.cli import main


def test_demo_mode():
    """Demo mode runs without error."""
    with patch.object(sys, "argv", ["cli", "demo"]):
        try:
            main()
        except SystemExit:
            pass


def test_export_json():
    """Export demo data as JSON."""
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / "test-export.json"
        with patch.object(sys, "argv", [
            "cli", "demo", "--output", str(out),
        ]):
            try:
                main()
            except SystemExit:
                pass
        assert out.exists()
        data = json.loads(out.read_text())
        assert "risks" in data
        assert "metadata" in data
        assert data["metadata"]["total_risks"] >= 12


def test_export_all_formats():
    """Demo --format all produces JSON, CSV, and PDF."""
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / "test-export.json"
        with patch.object(sys, "argv", [
            "cli", "demo", "--output", str(out), "--format", "all",
        ]):
            try:
                main()
            except SystemExit:
                pass
        json_path = Path(tmpdir) / "test-export.json"
        csv_path = Path(tmpdir) / "test-export.csv"
        pdf_path = Path(tmpdir) / "test-export.pdf"
        assert json_path.exists()
        assert csv_path.exists()
        assert pdf_path.exists()
        assert pdf_path.stat().st_size > 0
        # Verify JSON content
        data = json.loads(json_path.read_text())
        assert "risks" in data
        assert data["metadata"]["total_risks"] >= 12


def test_matrix_display():
    """Matrix prints without error."""
    # Create a demo and then run matrix
    with patch.object(sys, "argv", ["cli", "matrix"]):
        try:
            main()
        except SystemExit:
            pass

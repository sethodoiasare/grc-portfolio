"""Tests for CLI interface."""

import subprocess
import sys
import json
from pathlib import Path


def _run_cli(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "src.cli"] + args,
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent,
    )


class TestListTemplates:
    def test_list_templates_output(self):
        result = _run_cli(["list-templates"])
        assert result.returncode == 0
        assert "malware" in result.stdout
        assert "ransomware" in result.stdout
        assert "breach" in result.stdout
        assert "ddos" in result.stdout
        assert "insider" in result.stdout
        assert "credential" in result.stdout
        assert "6 templates available" in result.stdout


class TestDemoMode:
    def test_demo_generates_runbooks(self, tmp_path):
        output_dir = tmp_path / "demo_output"
        result = _run_cli(["generate", "--demo", "--output-dir", str(output_dir)])
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "PayFlow Ltd" in result.stdout
        assert "Ransomware Attack" in result.stdout
        assert "Data Breach" in result.stdout
        assert "Demo complete" in result.stdout

    def test_demo_creates_files(self, tmp_path):
        output_dir = tmp_path / "demo_output"
        result = _run_cli(["generate", "--demo", "--output-dir", str(output_dir)])
        assert result.returncode == 0
        files = list(output_dir.glob("*"))
        assert len(files) >= 2, f"Expected >=2 files, got {files}"

    def test_demo_markdown_has_org_name(self, tmp_path):
        output_dir = tmp_path / "demo_output"
        result = _run_cli(["generate", "--demo", "--output-dir", str(output_dir)])
        assert result.returncode == 0
        md_files = list(output_dir.glob("*.md"))
        assert len(md_files) > 0
        content = md_files[0].read_text()
        assert "PayFlow Ltd" in content


class TestGenerateCommand:
    def test_generate_single_type(self, tmp_path):
        output_dir = tmp_path / "output"
        result = _run_cli(["generate", "--type", "malware", "--severity", "SEV2",
                           "--output-dir", str(output_dir)])
        assert result.returncode == 0
        assert "Malware Outbreak" in result.stdout
        files = list(output_dir.glob("*"))
        assert len(files) >= 1

    def test_generate_json_format(self, tmp_path):
        output_dir = tmp_path / "output"
        result = _run_cli(["generate", "--type", "credential", "--format", "json",
                           "--output-dir", str(output_dir)])
        assert result.returncode == 0
        json_files = list(output_dir.glob("*.json"))
        assert len(json_files) == 1
        data = json.loads(json_files[0].read_text())
        assert data["incident_type"] == "credential"

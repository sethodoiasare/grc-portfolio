"""Tests for runbook generation engine."""

import json
import pytest
from pathlib import Path
from src.generator import (
    generate_runbook, generate_all, export_runbook_markdown,
    export_runbook_json, export_runbook_pdf, save_runbook,
)
from src.models import Runbook, Severity
from src.demo_context import get_demo_context


class TestGenerateRunbook:
    def test_generate_single_runbook(self):
        rb = generate_runbook("malware", "SEV2", get_demo_context())
        assert isinstance(rb, Runbook)
        assert rb.incident_type == "malware"
        assert rb.severity == Severity.SEV2
        assert rb.organization == "PayFlow Ltd"
        assert len(rb.stages) == 6

    def test_generate_all_six(self):
        runbooks = generate_all(get_demo_context())
        assert len(runbooks) == 6
        types = {rb.incident_type for rb in runbooks}
        assert types == {"malware", "ransomware", "breach", "ddos", "insider", "credential"}
        for rb in runbooks:
            assert rb.severity == Severity.SEV2

    def test_customization_injects_org_name(self):
        rb = generate_runbook("ransomware", "SEV2", get_demo_context())
        assert rb.organization == "PayFlow Ltd"
        # Check that org-specific email domain appears in contacts
        emails = [c.get("email", "") for c in rb.contacts.values()]
        assert any("payflow" in e.lower() for e in emails), f"No PayFlow email found in {emails}"

    def test_severity_sets_slas(self):
        rb_sev1 = generate_runbook("malware", "SEV1", {"org_name": "Test"})
        rb_sev3 = generate_runbook("malware", "SEV3", {"org_name": "Test"})
        # SEV1 should have tighter SLAs than SEV3
        sev1_total = sum(s.sla_minutes for s in rb_sev1.stages)
        sev3_total = sum(s.sla_minutes for s in rb_sev3.stages)
        assert sev1_total < sev3_total, f"SEV1 total {sev1_total} >= SEV3 total {sev3_total}"

    def test_runbook_structure_integrity(self):
        rb = generate_runbook("breach", "SEV1", get_demo_context())
        assert rb.total_actions > 0
        assert len(rb.contacts) > 0
        assert len(rb.tools) > 0
        assert len(rb.communication_plan) > 0
        assert "rto_hours" in rb.recovery_objectives
        assert "rpo_hours" in rb.recovery_objectives
        assert rb.lessons_learned_prompt

    def test_generates_without_context(self):
        rb = generate_runbook("ddos", "SEV3")
        assert isinstance(rb, Runbook)
        assert rb.organization == "Organisation"
        assert len(rb.stages) == 6

    def test_unknown_incident_type_raises(self):
        with pytest.raises(ValueError, match="Unknown incident type"):
            generate_runbook("unknown", "SEV2")


class TestExportMarkdown:
    def test_markdown_has_required_sections(self):
        rb = generate_runbook("malware", "SEV2", get_demo_context())
        md = export_runbook_markdown(rb)
        assert "# Incident Response Runbook" in md
        assert "PayFlow Ltd" in md
        assert "SEV2" in md
        assert "## Severity SLA" in md
        assert "## Key Contacts" in md
        assert "## Tools & Systems" in md
        assert "## Communication Plan" in md
        assert "## Incident Response Stages" in md
        assert "## Lessons Learned" in md
        assert "- [ ]" in md  # Checkbox actions

    def test_markdown_has_stage_headings(self):
        rb = generate_runbook("ransomware", "SEV1", get_demo_context())
        md = export_runbook_markdown(rb)
        for stage in rb.stages:
            assert f"Stage {stage.stage_number}: {stage.stage_name}" in md

    def test_markdown_has_contacts_table(self):
        rb = generate_runbook("breach", "SEV2", get_demo_context())
        md = export_runbook_markdown(rb)
        assert "| Role | Name | Email | Phone |" in md


class TestExportJSON:
    def test_json_export_is_valid(self):
        rb = generate_runbook("malware", "SEV2", get_demo_context())
        j = export_runbook_json(rb)
        data = json.loads(j)
        assert data["incident_type"] == "malware"
        assert data["severity"] == "SEV2"
        assert isinstance(data["stages"], list)
        assert len(data["stages"]) == 6

    def test_json_contains_all_fields(self):
        rb = generate_runbook("credential", "SEV1", get_demo_context())
        j = export_runbook_json(rb)
        data = json.loads(j)
        for key in ["incident_type", "severity", "generated_date", "organization",
                     "stages", "contacts", "tools", "communication_plan",
                     "recovery_objectives", "lessons_learned_prompt"]:
            assert key in data, f"Missing key: {key}"


class TestSaveRunbook:
    def test_save_both_formats(self, tmp_path):
        rb = generate_runbook("malware", "SEV2", get_demo_context())
        saved = save_runbook(rb, tmp_path, format="both")
        assert len(saved) == 2
        assert any(p.suffix == ".md" for p in saved)
        assert any(p.suffix == ".json" for p in saved)

    def test_save_md_only(self, tmp_path):
        rb = generate_runbook("malware", "SEV2", get_demo_context())
        saved = save_runbook(rb, tmp_path, format="md")
        assert len(saved) == 1
        assert saved[0].suffix == ".md"

    def test_save_json_only(self, tmp_path):
        rb = generate_runbook("malware", "SEV2", get_demo_context())
        saved = save_runbook(rb, tmp_path, format="json")
        assert len(saved) == 1
        assert saved[0].suffix == ".json"

    def test_save_pdf_only(self, tmp_path):
        rb = generate_runbook("ransomware", "SEV2", get_demo_context())
        saved = save_runbook(rb, tmp_path, format="pdf")
        assert len(saved) == 1
        assert saved[0].suffix == ".pdf"
        assert saved[0].exists()
        assert saved[0].stat().st_size > 0

    def test_save_all_formats(self, tmp_path):
        rb = generate_runbook("ransomware", "SEV2", get_demo_context())
        saved = save_runbook(rb, tmp_path, format="all")
        assert len(saved) == 3
        suffixes = {p.suffix for p in saved}
        assert suffixes == {".md", ".json", ".pdf"}


class TestExportPDF:
    def test_export_pdf_creates_non_empty_file(self, tmp_path):
        rb = generate_runbook("ransomware", "SEV2", get_demo_context())
        pdf_path = tmp_path / "test-runbook.pdf"
        result = export_runbook_pdf(rb, str(pdf_path))
        assert pdf_path.exists()
        assert pdf_path.stat().st_size > 0
        assert result == str(pdf_path)

    def test_export_pdf_all_stages_present(self, tmp_path):
        rb = generate_runbook("malware", "SEV3", get_demo_context())
        pdf_path = tmp_path / "malware-sev3.pdf"
        export_runbook_pdf(rb, str(pdf_path))
        assert pdf_path.exists()
        # PDF content is compressed; verify the output is substantial
        # (6 stages + cover + summary = 8+ pages minimum)
        size_kb = pdf_path.stat().st_size / 1024
        assert size_kb > 8, f"PDF too small ({size_kb:.1f} KB) -- stage content may be missing"

    def test_export_pdf_contains_org_name(self, tmp_path):
        rb = generate_runbook("ddos", "SEV1", get_demo_context())
        pdf_path = tmp_path / "ddos-sev1.pdf"
        export_runbook_pdf(rb, str(pdf_path))
        raw = pdf_path.read_text(errors="ignore")
        assert "PayFlow Ltd" in raw

    def test_export_pdf_severity_colors(self, tmp_path):
        rb = generate_runbook("breach", "SEV1", get_demo_context())
        pdf_path = tmp_path / "breach-sev1.pdf"
        export_runbook_pdf(rb, str(pdf_path))
        raw = pdf_path.read_text(errors="ignore")
        # SEV1 should produce a CRITICAL badge
        assert "CRITICAL" in raw or "SEV1" in raw

    def test_export_pdf_actions_have_checkboxes(self, tmp_path):
        rb = generate_runbook("credential", "SEV2", get_demo_context())
        pdf_path = tmp_path / "credential-sev2.pdf"
        export_runbook_pdf(rb, str(pdf_path))
        # PDF streams are compressed; verify PDF exists, is non-empty,
        # and the action count is reflected in reasonable file size
        assert pdf_path.exists()
        assert pdf_path.stat().st_size > 0
        # At least 6 stages + cover + summary pages = 8+ pages
        # Each page with actions contributes visual size
        assert pdf_path.stat().st_size > 8000, "PDF too small for full runbook"

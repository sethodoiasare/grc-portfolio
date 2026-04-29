"""Tests for reporter output generators."""

from pathlib import Path
from src.models import Question, CategoryScore, VendorAssessment, Answer, Weight, RiskRating
from src.scorer import assess_vendor
from src.reporter import print_assessment, save_report_json, save_report_md


def test_save_report_json_creates_file(tmp_path):
    questions = [
        Question(id="Q-001", category="AccessControl", text="MFA?", weight=Weight.HIGH, answer=Answer.YES),
    ]
    assessment = assess_vendor("TestCorp", questions)
    out = tmp_path / "report.json"
    path = save_report_json(assessment, str(out))
    assert Path(path).exists()
    import json
    data = json.loads(Path(path).read_text())
    assert data["vendor_name"] == "TestCorp"
    assert data["risk_rating"] == "LOW"


def test_save_report_md_creates_file(tmp_path):
    questions = [
        Question(id="Q-001", category="AccessControl", text="MFA?", weight=Weight.HIGH, answer=Answer.YES),
    ]
    assessment = assess_vendor("TestCorp", questions)
    out = tmp_path / "report.md"
    path = save_report_md(assessment, str(out))
    assert Path(path).exists()
    content = Path(path).read_text()
    assert "# Vendor Security Assessment: TestCorp" in content
    assert "Category Breakdown" in content


def test_print_assessment_does_not_crash():
    questions = [
        Question(id="Q-001", category="AccessControl", text="MFA?", weight=Weight.HIGH, answer=Answer.YES),
        Question(id="Q-002", category="Encryption", text="Enc at rest?", weight=Weight.HIGH, answer=Answer.NO, notes="Legacy"),
    ]
    assessment = assess_vendor("TestCorp", questions)
    # Should not raise
    print_assessment(assessment)


def test_json_report_structure(tmp_path):
    questions = [
        Question(id="Q-001", category="AccessControl", text="MFA?", weight=Weight.HIGH, answer=Answer.YES),
        Question(id="Q-002", category="Encryption", text="Enc at rest?", weight=Weight.HIGH, answer=Answer.NO, notes="Legacy"),
        Question(id="Q-003", category="Compliance", text="PCI DSS?", weight=Weight.LOW, answer=Answer.NA, notes="N/A"),
    ]
    assessment = assess_vendor("TestCorp", questions)
    out = tmp_path / "report.json"
    save_report_json(assessment, str(out))
    import json
    data = json.loads(out.read_text())

    assert len(data["questions"]) == 3
    assert len(data["category_scores"]) == 7
    assert len(data["top_risks"]) == 1  # Q-002 NO HIGH
    assert len(data["remediation_checklist"]) == 1  # only Q-002 needs remediation

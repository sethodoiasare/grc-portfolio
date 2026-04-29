"""Tests for CSV parser."""

import csv
import tempfile
from pathlib import Path

from src.parser import parse_questionnaire_csv, auto_detect_and_parse
from src.models import Answer, Weight


def test_parse_csv_basic():
    csv_content = (
        "category,question,weight,answer,notes\n"
        "AccessControl,MFA enforced?,HIGH,YES,Okta SSO\n"
        "DataProtection,Classification scheme?,HIGH,NO,Not implemented\n"
        "Encryption,Encryption at rest?,MEDIUM,PARTIAL,Legacy volumes\n"
    )
    tmp = Path(tempfile.mktemp(suffix=".csv"))
    tmp.write_text(csv_content)

    questions = parse_questionnaire_csv(str(tmp))
    assert len(questions) == 3

    assert questions[0].id == "Q-001"
    assert questions[0].category == "AccessControl"
    assert questions[0].text == "MFA enforced?"
    assert questions[0].weight == Weight.HIGH
    assert questions[0].answer == Answer.YES
    assert questions[0].notes == "Okta SSO"

    assert questions[1].answer == Answer.NO
    assert questions[2].answer == Answer.PARTIAL

    tmp.unlink()


def test_parse_csv_with_na():
    csv_content = (
        "category,question,weight,answer,notes\n"
        "Compliance,PCI DSS?,LOW,NA,Not applicable\n"
    )
    tmp = Path(tempfile.mktemp(suffix=".csv"))
    tmp.write_text(csv_content)

    questions = parse_questionnaire_csv(str(tmp))
    assert len(questions) == 1
    assert questions[0].answer == Answer.NA
    assert questions[0].is_scored() is False

    tmp.unlink()


def test_parse_csv_defaults():
    """Missing weight/answer columns should default to MEDIUM/YES."""
    csv_content = (
        "category,question\n"
        "AccessControl,Some question\n"
    )
    tmp = Path(tempfile.mktemp(suffix=".csv"))
    tmp.write_text(csv_content)

    questions = parse_questionnaire_csv(str(tmp))
    assert len(questions) == 1
    assert questions[0].weight == Weight.MEDIUM
    assert questions[0].answer == Answer.YES

    tmp.unlink()


def test_auto_detect_csv():
    csv_content = "category,question,weight,answer,notes\nAccessControl,MFA?,HIGH,YES,\n"
    tmp = Path(tempfile.mktemp(suffix=".csv"))
    tmp.write_text(csv_content)

    questions = auto_detect_and_parse(str(tmp))
    assert len(questions) == 1
    assert questions[0].category == "AccessControl"

    tmp.unlink()


def test_auto_detect_unsupported():
    try:
        auto_detect_and_parse("file.pdf")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Unsupported" in str(e)

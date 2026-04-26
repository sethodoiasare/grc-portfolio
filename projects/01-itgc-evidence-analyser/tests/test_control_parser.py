import pytest
from src.control_parser import ControlParser


@pytest.fixture
def parser():
    return ControlParser()


def test_list_controls_returns_all(parser):
    assert len(parser.list_controls()) == 58


def test_get_control_iam001_returns_dict(parser):
    control = parser.get_control("IAM_001")
    assert control is not None
    assert control["control_id"] == "IAM_001"
    assert control["domain"] == "IAM"
    assert len(control["d_statements"]) >= 4
    assert len(control["e_statements"]) >= 3


def test_get_control_unknown_returns_none(parser):
    assert parser.get_control("DOES_NOT_EXIST") is None


def test_get_by_domain_iam_returns_iam_controls_only(parser):
    iam_controls = parser.get_by_domain("IAM")
    assert len(iam_controls) > 0
    assert all(c["domain"] == "IAM" for c in iam_controls)


def test_get_by_domain_unknown_returns_empty(parser):
    assert parser.get_by_domain("NONEXISTENT") == []


def test_search_finds_privileged_controls(parser):
    results = parser.search("privileged")
    assert len(results) > 0


def test_search_case_insensitive(parser):
    lower = parser.search("access")
    upper = parser.search("ACCESS")
    assert len(lower) == len(upper)


def test_format_for_prompt_contains_d_statements(parser):
    text = parser.format_for_prompt("IAM_001", "D")
    assert "IAM_001" in text
    assert "D1" in text
    assert "D Statements" in text or "Design Requirements" in text


def test_format_for_prompt_contains_e_statements(parser):
    text = parser.format_for_prompt("IAM_001", "E")
    assert "E1" in text


def test_format_for_prompt_both(parser):
    text = parser.format_for_prompt("IAM_001", "both")
    assert "D1" in text
    assert "E1" in text


def test_format_for_prompt_unknown_raises(parser):
    with pytest.raises(ValueError, match="not found"):
        parser.format_for_prompt("FAKE_001")


def test_all_controls_have_required_keys(parser):
    required = {"control_id", "control_name", "vodafone_standard", "domain", "d_statements", "e_statements"}
    for c in parser.list_controls():
        assert required.issubset(c.keys()), f"{c.get('control_id')} missing keys"


def test_all_d_statements_have_id_and_text(parser):
    for c in parser.list_controls():
        for s in c["d_statements"]:
            assert "id" in s and "text" in s
            assert len(s["text"]) > 20

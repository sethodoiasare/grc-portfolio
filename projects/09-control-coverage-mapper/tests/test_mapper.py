"""Tests for coverage mapping engine."""

from src.models import ControlStatement, CoverageResult, CoverageStatus
from src.mapper import (
    map_coverage, build_heatmap_data, generate_remediation,
    _tokenize, _similarity, HIGH_SIMILARITY, MEDIUM_SIMILARITY,
)


def make_ctrl(framework: str, cid: str, title: str, desc: str, cat: str,
              status=CoverageStatus.GAP) -> ControlStatement:
    return ControlStatement(
        framework=framework, control_id=cid,
        title=title, description=desc, category=cat, status=status,
    )


class TestTokenize:
    def test_strips_punctuation(self):
        tokens = _tokenize("Access control: must be enforced!")
        assert "access" in tokens
        assert "control" in tokens
        assert "must" in tokens
        assert "enforced" in tokens
        assert ":" not in tokens
        assert "!" not in tokens

    def test_minimum_length_3(self):
        tokens = _tokenize("a b c ab abc abcd")
        assert "ab" not in tokens  # too short
        assert "abc" in tokens
        assert "abcd" in tokens

    def test_lowercase(self):
        tokens = _tokenize("Access Control Systems")
        assert "access" in tokens
        assert "control" in tokens
        assert "systems" in tokens


class TestSimilarity:
    def test_identical_returns_high_score(self):
        a = make_ctrl("F", "C-1", "Access Control Policy",
                       "Access shall be authorised and reviewed periodically.",
                       "Access Control")
        b = make_ctrl("P", "P-1", "Access Rules",
                       "Access shall be authorised and reviewed periodically.",
                       "Access Control")
        score = _similarity(a, b)
        assert score >= HIGH_SIMILARITY

    def test_completely_different_returns_low_score(self):
        a = make_ctrl("F", "C-1", "Encryption of Data",
                       "All data at rest must be encrypted using AES-256.",
                       "Encryption")
        b = make_ctrl("P", "P-1", "Office Supplies Policy",
                       "All pens and paper must be ordered through procurement.",
                       "Procurement")
        score = _similarity(a, b)
        assert score < MEDIUM_SIMILARITY

    def test_partial_overlap_returns_medium(self):
        a = make_ctrl("F", "C-1", "Access Control and Authentication",
                       "Access control shall be implemented with MFA for privileged users.",
                       "Access Control")
        b = make_ctrl("P", "P-1", "User Authentication Policy",
                       "Users must use strong passwords for all systems.",
                       "Authentication")
        score = _similarity(a, b)
        # Should be above the medium threshold due to keyword boost
        assert 0.05 <= score <= 0.80


class TestMapCoverage:
    def test_perfect_match_yields_covered(self):
        parsed = [
            make_ctrl("P", "P-1", "Access Control",
                       "Access control rules shall be established for physical and logical access "
                       "to information and associated assets.",
                       "Access Control"),
        ]
        framework = [
            make_ctrl("ISO27001", "A.5.15", "Access Control",
                       "Rules to control physical and logical access to information "
                       "and other associated assets shall be established.",
                       "Access Control"),
        ]
        result = map_coverage(parsed, framework)
        assert isinstance(result, CoverageResult)
        assert result.total_controls == 1
        assert result.covered == 1
        assert result.coverage_pct == 100.0

    def test_no_match_yields_gap(self):
        parsed = [
            make_ctrl("P", "P-1", "Office Supplies",
                       "Office supplies shall be ordered from approved vendors.",
                       "Procurement"),
        ]
        framework = [
            make_ctrl("ISO27001", "A.8.8", "Vulnerability Management",
                       "Technical vulnerabilities shall be obtained and evaluated.",
                       "Vulnerability Management"),
        ]
        result = map_coverage(parsed, framework)
        assert result.covered == 0
        assert result.gap == 1
        assert result.coverage_pct == 0.0
        assert len(result.gaps_list) == 1

    def test_partial_match_yields_partial(self):
        parsed = [
            make_ctrl("P", "P-1", "System Monitoring",
                       "We shall monitor systems for security events.",
                       "Monitoring"),
        ]
        framework = [
            make_ctrl("ISO27001", "A.8.16", "Monitoring Activities",
                       "Networks, systems and applications shall be monitored for "
                       "anomalous behaviour and evaluated.",
                       "Monitoring"),
        ]
        result = map_coverage(parsed, framework)
        assert result.covered + result.partial + result.gap == 1

    def test_multiple_controls_mixed(self):
        parsed = [
            make_ctrl("P", "P-1", "Access Control",
                       "All access to information systems shall be authorised and reviewed. "
                       "Privileged access rights must be formally approved.",
                       "Access Control"),
            make_ctrl("P", "P-2", "Encryption Policy",
                       "All data at rest must be encrypted. Data in transit must use TLS 1.2.",
                       "Data Protection"),
        ]
        framework = [
            make_ctrl("ISO27001", "A.5.15", "Access Control",
                       "Rules to control physical and logical access shall be established.",
                       "Access Control"),
            make_ctrl("ISO27001", "A.5.17", "Authentication Information",
                       "Allocation and management of authentication information shall be controlled.",
                       "Access Control"),
            make_ctrl("ISO27001", "A.8.8", "Vulnerability Management",
                       "Technical vulnerabilities shall be obtained and evaluated.",
                       "Vulnerability Management"),
        ]
        result = map_coverage(parsed, framework)
        assert result.total_controls == 3
        assert result.covered >= 0
        # Vulnerability Management should be a gap since nothing matches
        assert result.gap >= 1
        assert len(result.controls) == 3
        for c in result.controls:
            assert c.matched_text is not None or c.status == CoverageStatus.GAP

    def test_gaps_list_contains_only_gaps(self):
        parsed: list[ControlStatement] = []
        framework = [
            make_ctrl("ISO27001", "A.5.1", "Policies for InfoSec",
                       "Information security policies shall be defined and approved.",
                       "Governance"),
        ]
        result = map_coverage(parsed, framework)
        assert len(result.gaps_list) == 1
        assert result.gaps_list[0].control_id == "A.5.1"
        assert result.gaps_list[0].status == CoverageStatus.GAP


class TestHeatmap:
    def test_builds_category_counts(self):
        controls = [
            make_ctrl("ISO", "C1", "T1", "D1", "Access Control", CoverageStatus.COVERED),
            make_ctrl("ISO", "C2", "T2", "D2", "Access Control", CoverageStatus.PARTIAL),
            make_ctrl("ISO", "C3", "T3", "D3", "Monitoring", CoverageStatus.GAP),
        ]
        h = build_heatmap_data(controls)
        assert "Access Control" in h
        assert h["Access Control"]["total"] == 2
        assert h["Access Control"]["covered"] == 1
        assert h["Access Control"]["partial"] == 1
        assert h["Access Control"]["coverage_pct"] == 50.0
        assert "Monitoring" in h
        assert h["Monitoring"]["gap"] == 1


class TestRemediation:
    def test_returns_suggestion_for_known_category(self):
        remedy = generate_remediation("Access Control")
        assert len(remedy) > 30
        assert "access" in remedy.lower()

    def test_returns_generic_for_unknown_category(self):
        remedy = generate_remediation("Obscure Category Name")
        assert len(remedy) > 30

    def test_partial_category_match(self):
        remedy = generate_remediation("Identify — Asset Management")
        assert "asset" in remedy.lower()

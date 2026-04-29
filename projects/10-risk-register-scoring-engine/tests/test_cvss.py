"""Tests for CVSS v3.1 calculator."""

import pytest
from src.cvss_calc import parse_cvss_vector, calculate_cvss_score, get_severity
from src.models import (
    AttackVector, AttackComplexity, PrivilegesRequired, UserInteraction,
    Scope, CIAImpact, CVSSMetric,
)


class TestParseCVSSVector:
    def test_parse_critical_vector(self):
        """CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H -> 9.8"""
        m = parse_cvss_vector("AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H")
        assert m.av == AttackVector.NETWORK
        assert m.ac == AttackComplexity.LOW
        assert m.pr == PrivilegesRequired.NONE
        assert m.ui == UserInteraction.NONE
        assert m.s == Scope.UNCHANGED
        assert m.c == CIAImpact.HIGH
        assert m.i == CIAImpact.HIGH
        assert m.a == CIAImpact.HIGH

    def test_parse_with_cvss_prefix(self):
        """Strip CVSS:3.1/ prefix."""
        m = parse_cvss_vector("CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H")
        assert m.av == AttackVector.NETWORK

    def test_parse_all_av_values(self):
        """All four AttackVector values parse correctly."""
        for val, enum in [("N", AttackVector.NETWORK), ("A", AttackVector.ADJACENT),
                          ("L", AttackVector.LOCAL), ("P", AttackVector.PHYSICAL)]:
            m = parse_cvss_vector(f"AV:{val}/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:N")
            assert m.av == enum

    def test_parse_all_ac_values(self):
        for val, enum in [("L", AttackComplexity.LOW), ("H", AttackComplexity.HIGH)]:
            m = parse_cvss_vector(f"AV:N/AC:{val}/PR:N/UI:N/S:U/C:N/I:N/A:N")
            assert m.ac == enum

    def test_parse_all_cia_values(self):
        for val, enum in [("N", CIAImpact.NONE), ("L", CIAImpact.LOW), ("H", CIAImpact.HIGH)]:
            m = parse_cvss_vector(f"AV:N/AC:L/PR:N/UI:N/S:U/C:{val}/I:{val}/A:{val}")
            assert m.c == enum
            assert m.i == enum
            assert m.a == enum

    def test_parse_rejects_malformed(self):
        with pytest.raises(ValueError):
            parse_cvss_vector("not a vector")

    def test_parse_rejects_invalid_metric_value(self):
        with pytest.raises(ValueError):
            parse_cvss_vector("AV:X/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:N")

    def test_parse_rejects_missing_metric(self):
        with pytest.raises(ValueError):
            parse_cvss_vector("AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N")


class TestCalculateCVSSScore:
    def test_critical_9_8(self):
        """AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H = 9.8"""
        m = parse_cvss_vector("AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H")
        assert calculate_cvss_score(m) == 9.8

    def test_high_7_5(self):
        """AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:H = 7.5"""
        m = parse_cvss_vector("AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:H")
        assert calculate_cvss_score(m) == 7.5

    def test_zero_score(self):
        """AV:N/AC:H/PR:H/UI:R/S:U/C:N/I:N/A:N = 0.0 (no impact)"""
        m = parse_cvss_vector("AV:N/AC:H/PR:H/UI:R/S:U/C:N/I:N/A:N")
        assert calculate_cvss_score(m) == 0.0

    def test_scope_changed(self):
        """Scope changed should produce valid score."""
        m = parse_cvss_vector("AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H")
        score = calculate_cvss_score(m)
        assert 0.0 <= score <= 10.0

    def test_physical_local(self):
        """Physical access, local should reduce score."""
        m = parse_cvss_vector("AV:P/AC:H/PR:H/UI:R/S:U/C:H/I:H/A:H")
        score = calculate_cvss_score(m)
        assert 0.0 < score < 10.0

    def test_rounding_up(self):
        """Verify roundup to 1 decimal."""
        m = parse_cvss_vector("AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H")
        score = calculate_cvss_score(m)
        assert score == 9.8
        # Check it's exactly 1 decimal place
        assert score == round(score, 1)


class TestGetSeverity:
    def test_none_severity(self):
        assert get_severity(0.0) == "NONE"

    def test_low_boundaries(self):
        assert get_severity(0.1) == "LOW"
        assert get_severity(3.9) == "LOW"

    def test_medium_boundaries(self):
        assert get_severity(4.0) == "MEDIUM"
        assert get_severity(6.9) == "MEDIUM"

    def test_high_boundaries(self):
        assert get_severity(7.0) == "HIGH"
        assert get_severity(8.9) == "HIGH"

    def test_critical_boundary(self):
        assert get_severity(9.0) == "CRITICAL"
        assert get_severity(10.0) == "CRITICAL"

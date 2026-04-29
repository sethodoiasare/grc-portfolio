"""Tests for built-in control framework catalogs."""

import pytest
from src.frameworks import (
    iso27001_2022, nist_csf, cis_v8, vodafone_tier2,
    get_framework, list_frameworks,
    FRAMEWORK_REGISTRY,
)
from src.models import ControlStatement, CoverageStatus


class TestISO27001Framework:
    def test_has_minimum_controls(self):
        controls = iso27001_2022()
        assert len(controls) >= 10

    def test_controls_are_valid(self):
        controls = iso27001_2022()
        for c in controls:
            assert isinstance(c, ControlStatement)
            assert c.framework == "ISO27001"
            assert c.control_id.startswith("A.")
            assert len(c.title) > 5
            assert len(c.description) > 20
            assert len(c.category) > 0
            assert c.status == CoverageStatus.GAP

    def test_control_ids_are_iso_format(self):
        controls = iso27001_2022()
        for c in controls:
            # ISO control ids are like A.5.1, A.8.25
            parts = c.control_id.split(".")
            assert len(parts) >= 3
            assert parts[0] == "A"

    def test_categories_present(self):
        controls = iso27001_2022()
        cats = {c.category for c in controls}
        assert "Access Control" in cats or any("Access" in cat for cat in cats)
        assert len(cats) >= 5  # Multiple distinct categories


class TestNISTCSFFramework:
    def test_has_minimum_controls(self):
        controls = nist_csf()
        assert len(controls) >= 10

    def test_controls_are_valid(self):
        controls = nist_csf()
        for c in controls:
            assert isinstance(c, ControlStatement)
            assert c.framework == "NIST_CSF"
            assert "." in c.control_id
            assert len(c.title) > 5
            assert len(c.description) > 20
            assert c.status == CoverageStatus.GAP

    def test_covers_five_functions(self):
        controls = nist_csf()
        cats = {c.category for c in controls}
        # Should span Identify, Protect, Detect, Respond, Recover
        assert any("Identify" in cat for cat in cats)
        assert any("Protect" in cat for cat in cats)
        assert any("Detect" in cat for cat in cats)
        assert any("Respond" in cat for cat in cats)
        assert any("Recover" in cat for cat in cats)


class TestCISV8Framework:
    def test_has_minimum_controls(self):
        controls = cis_v8()
        assert len(controls) >= 10

    def test_controls_are_valid(self):
        controls = cis_v8()
        for c in controls:
            assert isinstance(c, ControlStatement)
            assert c.framework == "CIS_V8"
            assert c.control_id.startswith("CIS ")
            assert len(c.title) > 3
            assert len(c.description) > 15


class TestVodafoneFramework:
    def test_has_minimum_controls(self):
        controls = vodafone_tier2()
        assert len(controls) >= 10

    def test_controls_are_valid(self):
        controls = vodafone_tier2()
        for c in controls:
            assert isinstance(c, ControlStatement)
            assert c.framework == "VODAFONE"
            assert c.control_id.startswith("VOD-")
            assert len(c.title) > 5
            assert len(c.description) > 20

    def test_file_naming_pattern(self):
        controls = vodafone_tier2()
        for c in controls:
            parts = c.control_id.split("-")
            assert len(parts) == 3
            assert parts[0] == "VOD"
            assert parts[2].isdigit()


class TestFrameworkRegistry:
    def test_all_frameworks_registered(self):
        fws = list_frameworks()
        assert "ISO27001" in fws
        assert "NIST_CSF" in fws
        assert "CIS_V8" in fws
        assert "VODAFONE" in fws
        assert len(fws) == 4

    def test_get_framework_returns_fresh_copy(self):
        fw1 = get_framework("ISO27001")
        fw2 = get_framework("ISO27001")
        assert len(fw1) == len(fw2)
        assert fw1 is not fw2  # Fresh copy each time
        assert fw1[0].control_id == fw2[0].control_id

    def test_get_framework_case_insensitive(self):
        fw = get_framework("iso27001")
        assert fw[0].framework == "ISO27001"

    def test_get_framework_unknown_raises(self):
        with pytest.raises(KeyError):
            get_framework("NONEXISTENT_FRAMEWORK")

    def test_every_framework_returns_min_10_controls(self):
        for name in list_frameworks():
            controls = get_framework(name)
            assert len(controls) >= 10, f"{name} has fewer than 10 controls"

    def test_no_duplicate_control_ids_per_framework(self):
        for name in list_frameworks():
            controls = get_framework(name)
            ids = [c.control_id for c in controls]
            assert len(ids) == len(set(ids)), f"{name} has duplicate control IDs"

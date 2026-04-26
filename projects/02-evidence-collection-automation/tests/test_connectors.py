"""Tests for the connector engine and simulators."""

import pytest
from src.connectors import (
    ADSimulator, MDMSimulator, FirewallSimulator,
    VulnScannerSimulator, SIEMSimulator, DLPSimulator,
    ManualUploadConnector, CONNECTORS, get_connector,
)
from src.models import EvidenceItem


def test_all_connectors_registered():
    assert len(CONNECTORS) == 7
    assert "sim_ad" in CONNECTORS
    assert "sim_mdm" in CONNECTORS
    assert "sim_firewall" in CONNECTORS
    assert "sim_vuln" in CONNECTORS
    assert "sim_siem" in CONNECTORS
    assert "sim_dlp" in CONNECTORS
    assert "manual" in CONNECTORS


def test_get_connector():
    assert get_connector("sim_ad") is not None
    assert get_connector("nonexistent") is None


def test_ad_simulator_generates_evidence():
    items = ADSimulator().simulate("Czech Republic", {})
    assert len(items) >= 2
    assert all(isinstance(i, EvidenceItem) for i in items)
    assert any(i.evidence_type == "user_list" for i in items)
    assert any(i.evidence_type == "mfa_status" for i in items)
    assert any("IAM_001" in i.control_mapping for i in items)


def test_mdm_simulator_generates_evidence():
    items = MDMSimulator().simulate("Germany", {})
    assert len(items) >= 2
    types = {i.evidence_type for i in items}
    assert "device_compliance" in types


def test_firewall_simulator_generates_evidence():
    items = FirewallSimulator().simulate("Italy", {})
    assert len(items) >= 2
    types = {i.evidence_type for i in items}
    assert "firewall_rules" in types


def test_vuln_simulator_generates_evidence():
    items = VulnScannerSimulator().simulate("Spain", {})
    assert len(items) >= 1
    assert items[0].evidence_type == "vulnerability_list"


def test_siem_simulator_generates_evidence():
    items = SIEMSimulator().simulate("UK", {})
    assert len(items) >= 2


def test_dlp_simulator_generates_evidence():
    items = DLPSimulator().simulate("Ireland", {})
    assert len(items) >= 2


def test_manual_connector_generates_evidence():
    items = ManualUploadConnector().simulate("DRC", {"control_ids": ["IAM_001"]})
    assert len(items) == 1


def test_evidence_item_to_dict():
    item = EvidenceItem(
        evidence_type="user_list",
        source_system="Active Directory",
        data={"users": [{"name": "Test"}]},
        control_mapping=["IAM_001"],
    )
    d = item.to_dict()
    assert d["evidence_type"] == "user_list"
    assert d["source_system"] == "Active Directory"
    assert d["control_mapping"] == ["IAM_001"]


def test_evidence_item_to_json():
    item = EvidenceItem(evidence_type="test", source_system="test", data={})
    j = item.to_json()
    assert "test" in j
    assert "evidence_type" in j


def test_all_connectors_run_without_error():
    """Every registered connector should run and return valid items."""
    for ctype, connector in CONNECTORS.items():
        items = connector.simulate("Test Market", {})
        assert isinstance(items, list), f"{ctype} returned non-list"
        assert len(items) > 0, f"{ctype} returned 0 items"
        for item in items:
            assert isinstance(item, EvidenceItem)
            assert item.evidence_type
            assert item.source_system

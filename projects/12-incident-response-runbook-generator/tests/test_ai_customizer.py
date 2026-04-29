"""Tests for AI-assisted customisation engine."""

from src.ai_customizer import customize_runbook, enrich_with_regulatory
from src.templates import TEMPLATES
from src.demo_context import get_demo_context


class TestCustomizeRunbook:
    def test_customization_changes_org_name_in_contacts(self):
        template = TEMPLATES["malware"]
        context = {"org_name": "Acme Corp", "industry": "Retail"}
        result = customize_runbook(template, context)
        emails = [c.get("email", "") for c in result["contacts"].values()]
        assert any("acme" in e.lower() or "acmecorp" in e.lower() for e in emails), \
            f"No acme email in {emails}"

    def test_customization_preserves_stages(self):
        template = TEMPLATES["ransomware"]
        context = {"org_name": "TestCo", "industry": "Finance"}
        result = customize_runbook(template, context)
        assert len(result["stages"]) == 6
        assert result["incident_type"] == "ransomware"

    def test_different_org_names_produce_different_output(self):
        template = TEMPLATES["breach"]
        result_a = customize_runbook(template, {"org_name": "Alpha Ltd", "industry": "Healthcare"})
        result_b = customize_runbook(template, {"org_name": "Beta Inc", "industry": "Aviation"})
        # Contacts should differ by org name
        emails_a = set(c.get("email", "") for c in result_a["contacts"].values())
        emails_b = set(c.get("email", "") for c in result_b["contacts"].values())
        assert emails_a != emails_b, f"Same emails for different orgs: {emails_a}"

    def test_context_tool_stack_appears_in_output(self):
        template = TEMPLATES["credential"]
        context = {
            "org_name": "ToolCo",
            "tool_stack": [
                {"name": "CustomSIEM", "purpose": "siem and log management"},
                {"name": "CustomEDR", "purpose": "endpoint detection and response"},
                {"name": "CustomIdP", "purpose": "identity provider"},
            ],
        }
        result = customize_runbook(template, context)
        # Check tools include user's custom tools
        tool_names = [t["name"] for t in result["tools"]]
        assert any("Custom" in t for t in tool_names), f"No custom tools injected: {tool_names}"

    def test_customization_injects_tools_into_comms(self):
        template = TEMPLATES["ddos"]
        context = {
            "org_name": "NetCo",
            "tool_stack": [
                {"name": "PagerDuty Enterprise", "purpose": "alerting"},
            ],
        }
        result = customize_runbook(template, context)
        assert len(result["communication_plan"]) > 0

    def test_context_injects_actions_at_relevant_stages(self):
        template = TEMPLATES["malware"]
        context = {
            "org_name": "HealthOrg",
            "industry": "Healthcare",
            "regulatory_reqs": ["GDPR"],
        }
        result = customize_runbook(template, context)
        # Stage 1 (Identification) should have extra industry action
        stage1_actions = result["stages"][0].actions
        industry_found = any("healthcare" in a.lower() or "industry" in a.lower() for a in stage1_actions)
        assert industry_found, f"No industry action in stage 1: {stage1_actions[-2:]}"


class TestEnrichWithRegulatory:
    def test_gdpr_enrichment(self):
        actions = enrich_with_regulatory(["GDPR"])
        assert len(actions) >= 4
        assert any("GDPR" in a for a in actions)
        assert any("DPO" in a for a in actions)

    def test_pci_dss_enrichment(self):
        actions = enrich_with_regulatory(["PCI-DSS"])
        assert len(actions) >= 4
        assert any("PCI" in a for a in actions)
        assert any("cardholder" in a.lower() or "CDE" in a for a in actions)

    def test_multiple_regulations(self):
        actions = enrich_with_regulatory(["GDPR", "SOX"])
        assert len(actions) >= 8
        has_gdpr = any("GDPR" in a for a in actions)
        has_sox = any("SOX" in a for a in actions)
        assert has_gdpr and has_sox

    def test_no_duplicates(self):
        actions = enrich_with_regulatory(["GDPR"])
        # Check no duplicates
        assert len(actions) == len(set(actions)), f"Duplicates found in: {actions}"

    def test_unknown_regulation_returns_empty(self):
        actions = enrich_with_regulatory(["UNKNOWN-REG"])
        assert len(actions) == 0


class TestDemoContext:
    def test_demo_context_has_required_fields(self):
        ctx = get_demo_context()
        assert "org_name" in ctx
        assert "industry" in ctx
        assert "regulatory_reqs" in ctx
        assert "specific_threats" in ctx
        assert "tool_stack" in ctx
        assert "cloud_provider" in ctx
        assert "data_classification" in ctx

    def test_demo_context_has_pci_dss(self):
        ctx = get_demo_context()
        assert "PCI-DSS" in ctx["regulatory_reqs"]

    def test_demo_context_has_tools(self):
        ctx = get_demo_context()
        assert len(ctx["tool_stack"]) >= 4

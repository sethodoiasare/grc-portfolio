"""Tests for runbook templates."""

from src.templates import TEMPLATES, TEMPLATE_LIST
from src.models import IRStage


class TestTemplateRegistry:
    def test_all_six_templates_defined(self):
        expected = {"malware", "ransomware", "breach", "ddos", "insider", "credential"}
        assert set(TEMPLATES.keys()) == expected

    def test_template_list_matches(self):
        assert set(TEMPLATE_LIST) == set(TEMPLATES.keys())


class TestTemplateStructure:
    def test_each_template_has_six_stages(self):
        for name, template in TEMPLATES.items():
            assert len(template.base_stages) == 6, f"{name} has {len(template.base_stages)} stages, expected 6"

    def test_stages_have_correct_numbering(self):
        for name, template in TEMPLATES.items():
            for i, stage in enumerate(template.base_stages, start=1):
                assert stage.stage_number == i, f"{name} stage {i} has number {stage.stage_number}"

    def test_all_stages_have_actions(self):
        for name, template in TEMPLATES.items():
            for stage in template.base_stages:
                assert len(stage.actions) >= 5, (
                    f"{name} stage '{stage.stage_name}' has only {len(stage.actions)} actions, expected >= 5"
                )

    def test_all_stages_have_required_fields(self):
        required = ["stage_name", "description", "responsible_team", "escalation_trigger"]
        for name, template in TEMPLATES.items():
            for stage in template.base_stages:
                assert stage.stage_name, f"{name} stage {stage.stage_number}: empty stage_name"
                assert stage.description, f"{name} stage {stage.stage_number}: empty description"
                assert stage.responsible_team, f"{name} stage {stage.stage_number}: empty responsible_team"
                assert stage.escalation_trigger, f"{name} stage {stage.stage_number}: empty escalation_trigger"
                assert stage.sla_minutes > 0, f"{name} stage {stage.stage_number}: sla_minutes is {stage.sla_minutes}"

    def test_all_stages_are_ir_stage_instances(self):
        for name, template in TEMPLATES.items():
            for stage in template.base_stages:
                assert isinstance(stage, IRStage), f"{name} stage {stage.stage_number} is not IRStage"

    def test_templates_have_default_contacts(self):
        for name, template in TEMPLATES.items():
            assert len(template.default_contacts) >= 4, f"{name} has only {len(template.default_contacts)} contacts"

    def test_templates_have_default_tools(self):
        for name, template in TEMPLATES.items():
            assert len(template.default_tools) >= 4, f"{name} has only {len(template.default_tools)} tools"
            for tool in template.default_tools:
                assert "name" in tool, f"{name} tool missing name"
                assert "purpose" in tool, f"{name} tool missing purpose"

    def test_templates_have_comms_plan(self):
        for name, template in TEMPLATES.items():
            assert len(template.default_comms) >= 3, f"{name} has only {len(template.default_comms)} comms items"


class TestSpecificTemplates:
    def test_malware_stages_have_expected_names(self):
        template = TEMPLATES["malware"]
        expected_names = [
            "Identification", "Containment", "Eradication",
            "Recovery", "Post-Incident Analysis", "Lessons Learned & Closure",
        ]
        actual = [s.stage_name for s in template.base_stages]
        assert actual == expected_names

    def test_ransomware_stages_have_expected_names(self):
        template = TEMPLATES["ransomware"]
        expected_names = [
            "Identification", "Containment", "Eradication",
            "Recovery", "Post-Incident Analysis", "Lessons Learned & Closure",
        ]
        actual = [s.stage_name for s in template.base_stages]
        assert actual == expected_names

    def test_stages_follow_escalating_sla(self):
        """SLA should generally increase: identification is fast, lessons learned is slow."""
        for name, template in TEMPLATES.items():
            slas = [s.sla_minutes for s in template.base_stages]
            # Stage 1 should be the fastest, stage 6 the slowest
            assert slas[0] <= slas[-1], f"{name}: stage 1 SLA ({slas[0]}) > stage 6 SLA ({slas[-1]})"

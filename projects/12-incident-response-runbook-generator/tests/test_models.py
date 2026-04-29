"""Tests for domain models."""

from src.models import (
    IRStage, Runbook, RunbookTemplate, Severity, IncidentType,
    INCIDENT_TYPE_LABELS, SEVERITY_SLA,
)


class TestIRStage:
    def test_create_stage(self):
        stage = IRStage(
            stage_number=1,
            stage_name="Identification",
            description="Detect incident",
            actions=["Check alerts", "Interview users"],
            responsible_team="SOC",
            sla_minutes=15,
            escalation_trigger="Malware on >3 hosts",
        )
        assert stage.stage_number == 1
        assert stage.stage_name == "Identification"
        assert len(stage.actions) == 2
        assert stage.sla_minutes == 15

    def test_stage_to_dict(self):
        stage = IRStage(
            stage_number=2,
            stage_name="Containment",
            description="Stop spread",
            actions=["Isolate host"],
            responsible_team="CSIRT",
            sla_minutes=30,
            escalation_trigger="Spread detected",
        )
        d = stage.to_dict()
        assert d["stage_number"] == 2
        assert d["stage_name"] == "Containment"
        assert d["actions"] == ["Isolate host"]


class TestRunbook:
    def test_create_runbook(self):
        stages = [
            IRStage(1, "ID", "desc", ["act"], "team", 10, "trigger"),
            IRStage(2, "Contain", "desc2", ["act2"], "team2", 20, "trigger2"),
        ]
        rb = Runbook(
            incident_type="malware",
            severity=Severity.SEV1,
            generated_date="2026-04-29T10:00:00Z",
            organization="TestOrg",
            stages=stages,
            contacts={"SOC Lead": {"name": "John", "email": "j@t.com", "phone": "123"}},
            tools=[{"name": "EDR", "purpose": "Detection"}],
            communication_plan=["Notify CISO"],
            recovery_objectives={"rto_hours": 4, "rpo_hours": 1},
            lessons_learned_prompt="Review the incident",
        )
        assert rb.incident_type == "malware"
        assert rb.severity == Severity.SEV1
        assert rb.organization == "TestOrg"
        assert rb.total_actions == 2
        assert rb.total_sla_minutes == 30

    def test_total_actions_sums_correctly(self):
        stages = [
            IRStage(1, "S1", "d", ["a1", "a2", "a3"], "t", 10, "e"),
            IRStage(2, "S2", "d", ["a4", "a5"], "t", 20, "e"),
        ]
        rb = Runbook("malware", Severity.SEV2, "2026", "Org", stages)
        assert rb.total_actions == 5

    def test_to_dict_serializable(self):
        import json
        rb = Runbook(
            incident_type="malware",
            severity=Severity.SEV2,
            generated_date="2026",
            organization="TestOrg",
            stages=[],
        )
        d = rb.to_dict()
        assert d["severity"] == "SEV2"
        assert d["incident_type"] == "malware"
        json.dumps(d)


class TestRunbookTemplate:
    def test_create_template(self):
        stages = [
            IRStage(1, "ID", "d", ["a1", "a2"], "team", 10, "e"),
        ]
        tmpl = RunbookTemplate(
            incident_type="malware",
            base_stages=stages,
            default_contacts={"role": {"name": "N", "email": "E", "phone": "P"}},
            default_tools=[{"name": "T", "purpose": "P"}],
            default_comms=["Comm 1"],
        )
        assert tmpl.incident_type == "malware"
        assert len(tmpl.base_stages) == 1
        assert "role" in tmpl.default_contacts

    def test_template_to_dict(self):
        stages = [IRStage(1, "ID", "d", ["a1"], "team", 10, "e")]
        tmpl = RunbookTemplate("malware", stages, {}, [], [])
        d = tmpl.to_dict()
        assert isinstance(d["base_stages"], list)
        assert len(d["base_stages"]) == 1


class TestEnums:
    def test_severity_values(self):
        assert Severity.SEV1.value == "SEV1"
        assert Severity.SEV2.value == "SEV2"
        assert Severity.SEV3.value == "SEV3"

    def test_incident_type_values(self):
        assert IncidentType.MALWARE.value == "malware"
        assert IncidentType.BREACH.value == "breach"

    def test_labels_coverage(self):
        for it in ["malware", "ransomware", "breach", "ddos", "insider", "credential"]:
            assert it in INCIDENT_TYPE_LABELS

    def test_sla_overrides(self):
        for sev in Severity:
            sla = SEVERITY_SLA[sev]
            assert "response" in sla
            assert "containment" in sla
            assert "resolution" in sla
            assert sla["response"] <= sla["containment"] <= sla["resolution"]

"""Domain models for Incident Response Runbook Generator."""

from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime, timezone
from typing import Optional


class Severity(str, Enum):
    SEV1 = "SEV1"
    SEV2 = "SEV2"
    SEV3 = "SEV3"


class IncidentType(str, Enum):
    MALWARE = "malware"
    RANSOMWARE = "ransomware"
    BREACH = "breach"
    DDOS = "ddos"
    INSIDER = "insider"
    CREDENTIAL = "credential"


INCIDENT_TYPE_LABELS = {
    "malware": "Malware Outbreak",
    "ransomware": "Ransomware Attack",
    "breach": "Data Breach",
    "ddos": "DDoS Attack",
    "insider": "Insider Threat",
    "credential": "Credential Theft",
}

SEVERITY_SLA = {
    Severity.SEV1: {"response": 15, "containment": 60, "resolution": 240},
    Severity.SEV2: {"response": 30, "containment": 120, "resolution": 480},
    Severity.SEV3: {"response": 60, "containment": 240, "resolution": 1440},
}


@dataclass
class IRStage:
    """A single stage within an incident response runbook."""
    stage_number: int
    stage_name: str
    description: str
    actions: list[str]
    responsible_team: str
    sla_minutes: int
    escalation_trigger: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Runbook:
    """A complete incident response runbook for a specific incident type and severity."""
    incident_type: str
    severity: Severity
    generated_date: str
    organization: str
    stages: list[IRStage] = field(default_factory=list)
    contacts: dict = field(default_factory=dict)
    tools: list[dict] = field(default_factory=list)
    communication_plan: list[str] = field(default_factory=list)
    recovery_objectives: dict = field(default_factory=dict)
    lessons_learned_prompt: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        d["severity"] = self.severity.value
        d["stages"] = [s.to_dict() for s in self.stages]
        return d

    @property
    def total_actions(self) -> int:
        return sum(len(s.actions) for s in self.stages)

    @property
    def total_sla_minutes(self) -> int:
        return sum(s.sla_minutes for s in self.stages)


@dataclass
class RunbookTemplate:
    """A battle-tested template for a specific incident type."""
    incident_type: str
    base_stages: list[IRStage]
    default_contacts: dict
    default_tools: list[dict]
    default_comms: list[str]

    def to_dict(self) -> dict:
        return {
            "incident_type": self.incident_type,
            "base_stages": [s.to_dict() for s in self.base_stages],
            "default_contacts": self.default_contacts,
            "default_tools": self.default_tools,
            "default_comms": self.default_comms,
        }

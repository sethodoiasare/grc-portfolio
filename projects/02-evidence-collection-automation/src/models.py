"""
Domain models for the Evidence Collection Automator.

Defines core data structures for connectors, collections, evidence items,
and evidence bundles. Uses dataclasses with JSON serialisation.
"""

from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from typing import Optional
import json


class ConnectorStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"


class EvidenceItemType(str, Enum):
    USER_LIST = "user_list"
    MFA_STATUS = "mfa_status"
    GROUP_MEMBERSHIP = "group_membership"
    DEVICE_COMPLIANCE = "device_compliance"
    DEVICE_ENROLLMENT = "device_enrollment"
    OS_VERSION = "os_version"
    FIREWALL_RULES = "firewall_rules"
    VPN_CONFIG = "vpn_config"
    OPEN_PORTS = "open_ports"
    VULNERABILITY_LIST = "vulnerability_list"
    PATCH_STATUS = "patch_status"
    ALERT_VOLUME = "alert_volume"
    LOG_SOURCES = "log_sources"
    CORRELATION_RULES = "correlation_rules"
    DLP_EVENTS = "dlp_events"
    DLP_CHANNELS = "dlp_channels"
    DLP_RULESET = "dlp_ruleset"
    MANUAL_EVIDENCE = "manual_evidence"
    OTHER = "other"


@dataclass
class EvidenceItem:
    evidence_type: str
    source_system: str
    data: dict
    freshness_date: Optional[str] = None
    control_mapping: list[str] = field(default_factory=list)
    id: Optional[int] = None
    collection_id: Optional[int] = None
    normalized_at: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "collection_id": self.collection_id,
            "evidence_type": self.evidence_type,
            "source_system": self.source_system,
            "data": self.data,
            "freshness_date": self.freshness_date,
            "control_mapping": self.control_mapping,
            "normalized_at": self.normalized_at,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, default=str)


@dataclass
class EvidenceCollection:
    connector_id: int
    user_id: int
    market_id: Optional[int] = None
    control_ids: list[str] = field(default_factory=list)
    status: str = "running"
    id: Optional[int] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    evidence_count: int = 0
    summary: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "connector_id": self.connector_id,
            "user_id": self.user_id,
            "market_id": self.market_id,
            "control_ids": self.control_ids,
            "status": self.status,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "evidence_count": self.evidence_count,
            "summary": self.summary,
        }


@dataclass
class EvidenceBundle:
    user_id: int
    name: str
    description: str = ""
    item_ids: list[int] = field(default_factory=list)
    market_id: Optional[int] = None
    control_ids: list[str] = field(default_factory=list)
    id: Optional[int] = None
    created_at: Optional[str] = None
    exported_at: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "description": self.description,
            "item_ids": self.item_ids,
            "market_id": self.market_id,
            "control_ids": self.control_ids,
            "created_at": self.created_at,
            "exported_at": self.exported_at,
        }

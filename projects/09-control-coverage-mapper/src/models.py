"""Domain models for Security Control Coverage Mapper."""

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional


class Framework(str, Enum):
    ISO27001 = "ISO27001"
    NIST_CSF = "NIST_CSF"
    CIS_V8 = "CIS_V8"
    VODAFONE = "VODAFONE"


class CoverageStatus(str, Enum):
    COVERED = "COVERED"
    PARTIAL = "PARTIAL"
    GAP = "GAP"


@dataclass
class ControlStatement:
    framework: str
    control_id: str
    title: str
    description: str
    category: str
    status: CoverageStatus = CoverageStatus.GAP
    matched_text: Optional[str] = None
    similarity_score: float = 0.0

    def to_dict(self) -> dict:
        d = asdict(self)
        d["framework"] = self.framework
        d["status"] = self.status.value
        return d


@dataclass
class CoverageResult:
    framework: str
    total_controls: int
    covered: int = 0
    partial: int = 0
    gap: int = 0
    gaps_list: list[ControlStatement] = field(default_factory=list)
    heatmap_data: dict = field(default_factory=dict)
    controls: list[ControlStatement] = field(default_factory=list)

    @property
    def coverage_pct(self) -> float:
        if self.total_controls == 0:
            return 0.0
        return round(self.covered / self.total_controls * 100, 1)

    @property
    def effective_coverage_pct(self) -> float:
        """Coverage counting fully covered + 0.5 * partial."""
        if self.total_controls == 0:
            return 0.0
        return round((self.covered + 0.5 * self.partial) / self.total_controls * 100, 1)

    def rag_status(self) -> str:
        if self.coverage_pct >= 80:
            return "GREEN"
        elif self.coverage_pct >= 50:
            return "AMBER"
        return "RED"

    def to_dict(self) -> dict:
        return {
            "framework": self.framework,
            "total_controls": self.total_controls,
            "covered": self.covered,
            "partial": self.partial,
            "gap": self.gap,
            "coverage_pct": self.coverage_pct,
            "effective_coverage_pct": self.effective_coverage_pct,
            "rag_status": self.rag_status(),
            "heatmap_data": self.heatmap_data,
            "gaps_list": [g.to_dict() for g in self.gaps_list],
            "controls": [c.to_dict() for c in self.controls],
        }


@dataclass
class ParsedDocument:
    source_file: str
    paragraphs: list[str] = field(default_factory=list)
    extracted_controls: list[ControlStatement] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "source_file": self.source_file,
            "paragraph_count": len(self.paragraphs),
            "extracted_controls_count": len(self.extracted_controls),
            "extracted_controls": [c.to_dict() for c in self.extracted_controls],
        }

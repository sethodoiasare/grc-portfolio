"""Tests for data models."""

from src.models import (
    ProjectInfo,
    ProjectType,
    ProjectStatus,
    RAG,
    ControlCoverage,
    CoverageStatus,
    Deadline,
    SummaryStats,
    DashboardData,
    to_dict,
)

PS = ProjectStatus


def test_project_status_creation():
    p = ProjectInfo(
        project_id="P1",
        name="Test Project",
        type=ProjectType.WEB,
        status=PS.COMPLETE,
        test_count=42,
        last_audit_date="2026-01-01",
        controls_covered=["IAM"],
        evidence_freshness_days=7,
        rag=RAG.GREEN,
        description="A test project.",
    )
    assert p.project_id == "P1"
    assert p.test_count == 42
    assert p.rag == RAG.GREEN
    assert "IAM" in p.controls_covered


def test_control_coverage_creation():
    c = ControlCoverage(
        control_id="C01",
        control_name="User Registration",
        category="Access Control",
        covered_by=["P1", "P2"],
        status=CoverageStatus.PARTIAL,
        last_verified="2026-03-15",
    )
    assert c.control_id == "C01"
    assert c.status == CoverageStatus.PARTIAL
    assert len(c.covered_by) == 2


def test_deadline_creation():
    d = Deadline(
        id="DL1",
        description="Annual IAM Review",
        date="2026-05-15",
        days_remaining=14,
        related_control="C03",
        priority="HIGH",
    )
    assert d.days_remaining == 14
    assert d.priority == "HIGH"


def test_summary_stats():
    s = SummaryStats(
        total_projects=12,
        total_tests=738,
        controls_covered=28,
        controls_total=34,
        controls_gap=1,
        controls_partial=5,
        upcoming_deadlines=5,
        projects_green=8,
        projects_amber=3,
        projects_red=1,
    )
    assert s.total_projects == 12
    assert s.total_tests == 738


def test_dashboard_data():
    p = ProjectInfo("P1", "Test", ProjectType.CLI, PS.COMPLETE, 10, "2026-01-01", ["IAM"], 5, RAG.GREEN)
    c = ControlCoverage("C01", "Test Ctrl", "Test Cat", ["P1"], CoverageStatus.COVERED, "2026-01-01")
    d = Deadline("DL1", "Test DL", "2026-06-01", 30, "C01", "MEDIUM")
    s = SummaryStats(1, 10, 1, 1, 0, 0, 1, 1, 0, 0)
    dd = DashboardData(projects=[p], controls=[c], deadlines=[d], overall_rag=RAG.GREEN, summary=s)
    assert dd.overall_rag == RAG.GREEN
    assert len(dd.projects) == 1
    assert len(dd.controls) == 1
    assert dd.summary.total_projects == 1


def test_to_dict_converts_enums():
    p = ProjectInfo("P1", "Test", ProjectType.CLI, PS.COMPLETE, 10, "2026-01-01", ["IAM"], 5, RAG.GREEN)
    d = to_dict(p)
    assert d["project_id"] == "P1"
    assert d["type"] == "CLI"
    assert d["rag"] == "GREEN"
    assert not isinstance(d["type"], ProjectType)


def test_to_dict_nested():
    p = ProjectInfo("P1", "Test", ProjectType.WEB, PS.NEEDS_REVIEW, 10, "2026-01-01", ["IAM"], 15, RAG.AMBER)
    dd = DashboardData(projects=[p], controls=[], deadlines=[], overall_rag=RAG.AMBER)
    d = to_dict(dd)
    assert d["overall_rag"] == "AMBER"
    assert d["projects"][0]["rag"] == "AMBER"
    assert d["projects"][0]["status"] == "NEEDS_REVIEW"

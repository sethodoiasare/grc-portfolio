"""Tests for demo data and CLI entry point."""

from src.demo_data import get_dashboard_data, get_projects, get_controls, get_deadlines
from src.models import RAG, CoverageStatus


def test_demo_data_loads_projects():
    projects = get_projects()
    assert len(projects) == 12
    ids = {p.project_id for p in projects}
    assert ids == {f"P{i}" for i in range(1, 13)}


def test_demo_data_loads_controls():
    controls = get_controls()
    assert len(controls) >= 30
    covered = sum(1 for c in controls if c.status == CoverageStatus.COVERED)
    partial = sum(1 for c in controls if c.status == CoverageStatus.PARTIAL)
    gap = sum(1 for c in controls if c.status == CoverageStatus.GAP)
    assert covered + partial + gap == len(controls)
    assert gap > 0  # Realism: some gaps
    assert partial > 0  # Realism: some partial coverage


def test_demo_data_loads_deadlines():
    deadlines = get_deadlines()
    assert len(deadlines) == 5
    # Check sorted by days_remaining
    days = [d.days_remaining for d in deadlines]
    assert days == sorted(days)


def test_demo_dashboard_data():
    data = get_dashboard_data()
    assert len(data.projects) == 12
    assert len(data.controls) >= 30
    assert len(data.deadlines) == 5
    assert data.overall_rag in (RAG.GREEN, RAG.AMBER, RAG.RED)
    assert data.summary is not None
    assert data.summary.total_tests > 700
    assert data.summary.total_projects == 12
    assert data.generated_at != ""

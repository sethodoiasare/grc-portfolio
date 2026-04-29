"""Tests for domain models."""

from src.models import (
    ControlStatement, CoverageResult, ParsedDocument,
    CoverageStatus, Framework,
)


class TestControlStatement:
    def test_create_minimal(self):
        c = ControlStatement(
            framework="ISO27001",
            control_id="A.5.1",
            title="Test Control",
            description="A test control description.",
            category="Access Control",
        )
        assert c.framework == "ISO27001"
        assert c.control_id == "A.5.1"
        assert c.status == CoverageStatus.GAP
        assert c.similarity_score == 0.0
        assert c.matched_text is None

    def test_create_covered(self):
        c = ControlStatement(
            framework="NIST_CSF",
            control_id="ID.AM-2",
            title="Asset Inventory",
            description="Keep asset inventory.",
            category="Asset Management",
            status=CoverageStatus.COVERED,
            matched_text="All assets shall be inventoried.",
            similarity_score=0.85,
        )
        assert c.status == CoverageStatus.COVERED
        assert c.matched_text == "All assets shall be inventoried."
        assert c.similarity_score == 0.85

    def test_to_dict(self):
        c = ControlStatement(
            framework="CIS_V8",
            control_id="CIS 1.1",
            title="Inventory",
            description="Inventory all assets.",
            category="Inventory",
            status=CoverageStatus.PARTIAL,
            matched_text="Partial match",
            similarity_score=0.35,
        )
        d = c.to_dict()
        assert d["framework"] == "CIS_V8"
        assert d["control_id"] == "CIS 1.1"
        assert d["status"] == "PARTIAL"
        assert d["similarity_score"] == 0.35


class TestCoverageResult:
    def test_coverage_pct(self):
        r = CoverageResult(
            framework="ISO27001",
            total_controls=10,
            covered=8,
            partial=1,
            gap=1,
        )
        assert r.coverage_pct == 80.0

    def test_effective_coverage_pct(self):
        r = CoverageResult(
            framework="ISO27001",
            total_controls=10,
            covered=5,
            partial=2,
            gap=3,
        )
        # 5 + 0.5*2 = 6 / 10 = 60%
        assert r.effective_coverage_pct == 60.0

    def test_coverage_pct_zero_controls(self):
        r = CoverageResult(framework="NIST_CSF", total_controls=0)
        assert r.coverage_pct == 0.0
        assert r.effective_coverage_pct == 0.0

    def test_rag_green(self):
        r = CoverageResult(framework="F", total_controls=10, covered=9)
        assert r.rag_status() == "GREEN"

    def test_rag_amber(self):
        r = CoverageResult(framework="F", total_controls=10, covered=6)
        assert r.rag_status() == "AMBER"

    def test_rag_red(self):
        r = CoverageResult(framework="F", total_controls=10, covered=4)
        assert r.rag_status() == "RED"

    def test_to_dict(self):
        r = CoverageResult(
            framework="CIS_V8",
            total_controls=5,
            covered=3,
            partial=1,
            gap=1,
            heatmap_data={"Access": {"total": 5, "coverage_pct": 60.0, "covered": 3, "partial": 1, "gap": 1}},
        )
        d = r.to_dict()
        assert d["framework"] == "CIS_V8"
        assert d["total_controls"] == 5
        assert d["coverage_pct"] == 60.0
        assert d["rag_status"] == "AMBER"
        assert "Access" in d["heatmap_data"]


class TestParsedDocument:
    def test_create(self):
        doc = ParsedDocument(
            source_file="/tmp/policy.txt",
            paragraphs=["Para 1", "Para 2"],
        )
        assert doc.source_file == "/tmp/policy.txt"
        assert len(doc.paragraphs) == 2
        assert len(doc.extracted_controls) == 0

    def test_to_dict(self):
        doc = ParsedDocument(
            source_file="test.txt",
            paragraphs=["p1", "p2"],
            extracted_controls=[
                ControlStatement(
                    framework="PARSED", control_id="P-1",
                    title="T1", description="D1", category="C1",
                    status=CoverageStatus.GAP,
                ),
            ],
        )
        d = doc.to_dict()
        assert d["source_file"] == "test.txt"
        assert d["paragraph_count"] == 2
        assert d["extracted_controls_count"] == 1


class TestFrameworkEnum:
    def test_values(self):
        assert Framework.ISO27001.value == "ISO27001"
        assert Framework.NIST_CSF.value == "NIST_CSF"
        assert Framework.CIS_V8.value == "CIS_V8"
        assert Framework.VODAFONE.value == "VODAFONE"


class TestCoverageStatusEnum:
    def test_values(self):
        assert CoverageStatus.COVERED.value == "COVERED"
        assert CoverageStatus.PARTIAL.value == "PARTIAL"
        assert CoverageStatus.GAP.value == "GAP"

"""Tests for risk register operations."""

from datetime import date, timedelta
import pytest
from src.models import (
    Risk, RiskRegister, RiskCategory, RiskStatus, RiskLevel,
    SSVCMetric, Exploitation, Automatable, TechnicalImpact, MissionImpact,
)
from src.register import (
    create_risk, add_to_register, update_risk, accept_risk,
    mitigate_risk, close_risk, filter_by_status, filter_by_category,
    filter_by_level, get_overdue_reviews, get_risk_matrix, _compute_risk_level,
)


class TestCreateRisk:
    def test_create_basic_risk(self):
        ssvc = SSVCMetric(
            exploitation=Exploitation.POC,
            automatable=Automatable.YES,
            technical_impact=TechnicalImpact.TOTAL,
            mission_impact=MissionImpact.HIGH,
        )
        risk = create_risk(
            title="Test Risk",
            description="Description",
            category=RiskCategory.APPLICATION,
            cvss_vector="AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
            ssvc_metric=ssvc,
            owner="tester",
        )
        assert risk.title == "Test Risk"
        assert risk.cvss_score == 9.8
        assert risk.ssvc_decision.value == "ACT"
        assert risk.status == RiskStatus.IDENTIFIED

    def test_create_risk_uses_today(self):
        ssvc = SSVCMetric(Exploitation.NONE, Automatable.NO, TechnicalImpact.PARTIAL, MissionImpact.LOW)
        risk = create_risk("T", "D", RiskCategory.DATA, "AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:L/A:L", ssvc)
        assert risk.identified_date == date.today()

    def test_create_risk_with_controls(self):
        ssvc = SSVCMetric(Exploitation.NONE, Automatable.NO, TechnicalImpact.PARTIAL, MissionImpact.LOW)
        risk = create_risk(
            "T", "D", RiskCategory.INFRASTRUCTURE,
            "AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:L/A:L",
            ssvc, control_mapping=["IAM-001", "IAM-002"],
        )
        assert len(risk.control_mapping) == 2

    def test_create_risk_computes_level(self):
        ssvc = SSVCMetric(Exploitation.NONE, Automatable.NO, TechnicalImpact.PARTIAL, MissionImpact.LOW)
        # impact=95, likelihood=85 -> bins 5x5 -> 25 -> CRITICAL
        risk = create_risk(
            "T", "D", RiskCategory.APPLICATION,
            "AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:L/A:L",
            ssvc, impact_score=95, likelihood_score=85,
        )
        assert risk.risk_level == RiskLevel.CRITICAL

        # impact=20, likelihood=20 -> bins 1x1 -> 1 -> LOW
        risk2 = create_risk(
            "T2", "D2", RiskCategory.APPLICATION,
            "AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:L/A:L",
            ssvc, impact_score=20, likelihood_score=20,
        )
        assert risk2.risk_level == RiskLevel.LOW


class TestAddToRegister:
    def test_auto_assigns_id(self):
        reg = RiskRegister()
        ssvc = SSVCMetric(Exploitation.NONE, Automatable.NO, TechnicalImpact.PARTIAL, MissionImpact.LOW)
        risk = create_risk("T", "D", RiskCategory.DATA, "AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:L/A:L", ssvc)
        result = add_to_register(reg, risk)
        assert result.risk_id == "RSK-001"
        assert len(reg.risks) == 1

    def test_sequential_ids(self):
        reg = RiskRegister()
        ssvc = SSVCMetric(Exploitation.NONE, Automatable.NO, TechnicalImpact.PARTIAL, MissionImpact.LOW)
        r1 = add_to_register(reg, create_risk("A", "D", RiskCategory.DATA, "AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:L/A:L", ssvc))
        r2 = add_to_register(reg, create_risk("B", "D", RiskCategory.DATA, "AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:L/A:L", ssvc))
        r3 = add_to_register(reg, create_risk("C", "D", RiskCategory.DATA, "AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:L/A:L", ssvc))
        assert r1.risk_id == "RSK-001"
        assert r2.risk_id == "RSK-002"
        assert r3.risk_id == "RSK-003"


class TestUpdateRisk:
    def test_update_fields(self):
        reg = RiskRegister()
        ssvc = SSVCMetric(Exploitation.NONE, Automatable.NO, TechnicalImpact.PARTIAL, MissionImpact.LOW)
        risk = add_to_register(reg, create_risk("T", "D", RiskCategory.DATA, "AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:L/A:L", ssvc))
        updated = update_risk(reg, "RSK-001", {"title": "New Title", "owner": "alice"})
        assert updated is not None
        assert updated.title == "New Title"
        assert updated.owner == "alice"

    def test_update_nonexistent(self):
        reg = RiskRegister()
        result = update_risk(reg, "RSK-999", {"title": "X"})
        assert result is None

    def test_update_recomputes_level(self):
        reg = RiskRegister()
        ssvc = SSVCMetric(Exploitation.NONE, Automatable.NO, TechnicalImpact.PARTIAL, MissionImpact.LOW)
        risk = add_to_register(reg, create_risk(
            "T", "D", RiskCategory.DATA, "AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:L/A:L",
            ssvc, impact_score=20, likelihood_score=20,
        ))
        assert risk.risk_level == RiskLevel.LOW
        update_risk(reg, "RSK-001", {"impact_score": 95, "likelihood_score": 95})
        assert risk.risk_level == RiskLevel.CRITICAL


class TestAcceptRisk:
    def test_accept_workflow(self):
        ssvc = SSVCMetric(Exploitation.NONE, Automatable.NO, TechnicalImpact.PARTIAL, MissionImpact.LOW)
        risk = create_risk("T", "D", RiskCategory.DATA, "AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:L/A:L", ssvc)
        accept_risk(risk, "Business decision", "cto", review_days=30)
        assert risk.status == RiskStatus.ACCEPTED
        assert risk.acceptance_rationale == "Business decision"
        assert risk.owner == "cto"
        assert risk.review_date == date.today() + timedelta(days=30)


class TestMitigateAndClose:
    def test_mitigate_workflow(self):
        ssvc = SSVCMetric(Exploitation.NONE, Automatable.NO, TechnicalImpact.PARTIAL, MissionImpact.LOW)
        risk = create_risk("T", "D", RiskCategory.DATA, "AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:L/A:L", ssvc)
        mitigate_risk(risk, "Apply patch X")
        assert risk.status == RiskStatus.MITIGATED
        assert risk.treatment_plan == "Apply patch X"

    def test_close_workflow(self):
        ssvc = SSVCMetric(Exploitation.NONE, Automatable.NO, TechnicalImpact.PARTIAL, MissionImpact.LOW)
        risk = create_risk("T", "D", RiskCategory.DATA, "AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:L/A:L", ssvc)
        close_risk(risk)
        assert risk.status == RiskStatus.CLOSED


class TestFiltering:
    def test_filter_by_status(self):
        reg = RiskRegister()
        ssvc = SSVCMetric(Exploitation.NONE, Automatable.NO, TechnicalImpact.PARTIAL, MissionImpact.LOW)
        r1 = add_to_register(reg, create_risk("A", "D", RiskCategory.DATA, "AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:L/A:L", ssvc))
        r2 = add_to_register(reg, create_risk("B", "D", RiskCategory.DATA, "AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:L/A:L", ssvc))
        close_risk(r2)
        assert len(filter_by_status(reg, RiskStatus.IDENTIFIED)) == 1
        assert len(filter_by_status(reg, RiskStatus.CLOSED)) == 1

    def test_filter_by_category(self):
        reg = RiskRegister()
        ssvc = SSVCMetric(Exploitation.NONE, Automatable.NO, TechnicalImpact.PARTIAL, MissionImpact.LOW)
        add_to_register(reg, create_risk("A", "D", RiskCategory.DATA, "AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:L/A:L", ssvc))
        add_to_register(reg, create_risk("B", "D", RiskCategory.APPLICATION, "AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:L/A:L", ssvc))
        assert len(filter_by_category(reg, RiskCategory.DATA)) == 1
        assert len(filter_by_category(reg, RiskCategory.APPLICATION)) == 1
        assert len(filter_by_category(reg, RiskCategory.VENDOR)) == 0

    def test_filter_by_level(self):
        reg = RiskRegister()
        ssvc = SSVCMetric(Exploitation.NONE, Automatable.NO, TechnicalImpact.PARTIAL, MissionImpact.LOW)
        add_to_register(reg, create_risk(
            "A", "D", RiskCategory.DATA, "AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:L/A:L",
            ssvc, impact_score=95, likelihood_score=95,
        ))  # CRITICAL
        add_to_register(reg, create_risk(
            "B", "D", RiskCategory.DATA, "AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:L/A:L",
            ssvc, impact_score=20, likelihood_score=20,
        ))  # LOW
        assert len(filter_by_level(reg, RiskLevel.CRITICAL)) == 1
        assert len(filter_by_level(reg, RiskLevel.LOW)) == 1
        assert len(filter_by_level(reg, RiskLevel.HIGH)) == 0


class TestOverdueReviews:
    def test_overdue_reviews(self):
        reg = RiskRegister()
        ssvc = SSVCMetric(Exploitation.NONE, Automatable.NO, TechnicalImpact.PARTIAL, MissionImpact.LOW)
        r1 = add_to_register(reg, create_risk("A", "D", RiskCategory.DATA, "AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:L/A:L", ssvc))
        accept_risk(r1, "reason", "cto", review_days=1)
        # Manually set review date to the past
        r1.review_date = date.today() - timedelta(days=10)

        r2 = add_to_register(reg, create_risk("B", "D", RiskCategory.DATA, "AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:L/A:L", ssvc))
        accept_risk(r2, "reason", "cto", review_days=365)

        overdue = get_overdue_reviews(reg)
        assert len(overdue) == 1
        assert overdue[0].risk_id == "RSK-001"


class TestRiskMatrix:
    def test_matrix_structure(self):
        reg = RiskRegister()
        ssvc = SSVCMetric(Exploitation.NONE, Automatable.NO, TechnicalImpact.PARTIAL, MissionImpact.LOW)
        # Add risks in various positions
        add_to_register(reg, create_risk(
            "A", "D", RiskCategory.DATA, "AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:L/A:L",
            ssvc, impact_score=95, likelihood_score=95,
        ))  # cell 5,5 -> CRITICAL
        add_to_register(reg, create_risk(
            "B", "D", RiskCategory.DATA, "AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:L/A:L",
            ssvc, impact_score=20, likelihood_score=20,
        ))  # cell 1,1 -> LOW

        matrix = get_risk_matrix(reg)
        assert len(matrix["cells"]) == 5
        assert all(len(row) == 5 for row in matrix["cells"])
        # Cell [4][4] = likelihood 5, impact 5
        assert matrix["cells"][4][4] == 1
        # Cell [0][0] = likelihood 1, impact 1
        assert matrix["cells"][0][0] == 1
        assert "L5-I5" in matrix["risks_by_cell"]
        assert "L1-I1" in matrix["risks_by_cell"]

    def test_matrix_total_matches_register(self):
        reg = RiskRegister()
        ssvc = SSVCMetric(Exploitation.NONE, Automatable.NO, TechnicalImpact.PARTIAL, MissionImpact.LOW)
        for i in range(5):
            add_to_register(reg, create_risk(
                f"R{i}", "D", RiskCategory.DATA,
                "AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:L/A:L", ssvc,
            ))
        matrix = get_risk_matrix(reg)
        total = sum(sum(row) for row in matrix["cells"])
        assert total == len(reg.risks)


class TestComputeRiskLevel:
    def test_level_boundaries(self):
        # LOW: 1-4
        assert _compute_risk_level(20, 20) == RiskLevel.LOW
        assert _compute_risk_level(40, 10) == RiskLevel.LOW  # bin 2 * 1 = 2
        # MEDIUM: 5-9
        assert _compute_risk_level(50, 30) == RiskLevel.MEDIUM  # bin 3 * 2 = 6
        assert _compute_risk_level(50, 50) == RiskLevel.MEDIUM  # bin 3 * 3 = 9
        # HIGH: 10-19
        assert _compute_risk_level(50, 80) == RiskLevel.HIGH  # bin 3 * 4 = 12
        assert _compute_risk_level(80, 50) == RiskLevel.HIGH  # bin 4 * 3 = 12
        # CRITICAL: 20-25
        assert _compute_risk_level(80, 80) == RiskLevel.HIGH  # bin 4 * 4 = 16 -> HIGH (10-19)
        assert _compute_risk_level(95, 85) == RiskLevel.CRITICAL  # bin 5 * 5 = 25

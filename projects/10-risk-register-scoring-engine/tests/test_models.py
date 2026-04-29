"""Tests for data models."""

from datetime import date
from src.models import (
    Risk, RiskRegister, RiskCategory, RiskStatus, RiskLevel,
    CVSSMetric, SSVCMetric, AttackVector, AttackComplexity,
    PrivilegesRequired, UserInteraction, Scope, CIAImpact,
    Exploitation, Automatable, TechnicalImpact, MissionImpact,
    SSVCDecision,
)


class TestRiskModel:
    def test_create_risk_minimal(self):
        risk = Risk(
            risk_id="RSK-001",
            title="Test Risk",
            description="A test risk",
            category=RiskCategory.APPLICATION,
            owner="tester",
            identified_date=date.today(),
            status=RiskStatus.IDENTIFIED,
            cvss_score=7.5,
            cvss_vector="AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:H",
            ssvc_decision=SSVCDecision.ATTEND,
            impact_score=60,
            likelihood_score=50,
            risk_level=RiskLevel.HIGH,
        )
        assert risk.risk_id == "RSK-001"
        assert risk.title == "Test Risk"
        assert risk.cvss_score == 7.5
        assert risk.risk_level == RiskLevel.HIGH

    def test_risk_with_optional_fields(self):
        risk = Risk(
            risk_id="RSK-002",
            title="Accepted Risk",
            description="Accepted with rationale",
            category=RiskCategory.VENDOR,
            owner="cto",
            identified_date=date(2025, 1, 15),
            status=RiskStatus.ACCEPTED,
            cvss_score=5.5,
            cvss_vector="AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:L/A:L",
            ssvc_decision=SSVCDecision.TRACK_STAR,
            impact_score=40,
            likelihood_score=30,
            risk_level=RiskLevel.MEDIUM,
            acceptance_rationale="Business justification",
            treatment_plan="Compensating controls",
            review_date=date(2025, 12, 31),
            control_mapping=["CTRL-001", "CTRL-002"],
        )
        assert risk.acceptance_rationale == "Business justification"
        assert risk.review_date == date(2025, 12, 31)
        assert len(risk.control_mapping) == 2

    def test_all_categories(self):
        for cat in RiskCategory:
            risk = Risk(
                risk_id="RSK-099", title="X", description="X",
                category=cat, owner="x", identified_date=date.today(),
                status=RiskStatus.IDENTIFIED, cvss_score=5.0,
                cvss_vector="AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:L/A:L",
                ssvc_decision=SSVCDecision.TRACK,
                impact_score=50, likelihood_score=50, risk_level=RiskLevel.MEDIUM,
            )
            assert risk.category == cat

    def test_all_statuses(self):
        for st in RiskStatus:
            risk = Risk(
                risk_id="RSK-099", title="X", description="X",
                category=RiskCategory.APPLICATION, owner="x",
                identified_date=date.today(), status=st, cvss_score=5.0,
                cvss_vector="AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:L/A:L",
                ssvc_decision=SSVCDecision.TRACK,
                impact_score=50, likelihood_score=50, risk_level=RiskLevel.MEDIUM,
            )
            assert risk.status == st

    def test_all_levels(self):
        for lvl in RiskLevel:
            risk = Risk(
                risk_id="RSK-099", title="X", description="X",
                category=RiskCategory.APPLICATION, owner="x",
                identified_date=date.today(), status=RiskStatus.IDENTIFIED,
                cvss_score=5.0,
                cvss_vector="AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:L/A:L",
                ssvc_decision=SSVCDecision.TRACK,
                impact_score=50, likelihood_score=50, risk_level=lvl,
            )
            assert risk.risk_level == lvl


class TestRiskRegisterModel:
    def test_empty_register(self):
        reg = RiskRegister(owner="GRC")
        assert len(reg.risks) == 0
        assert reg.owner == "GRC"

    def test_add_risk(self):
        reg = RiskRegister()
        risk = Risk(
            risk_id="RSK-001", title="T", description="D",
            category=RiskCategory.DATA, owner="o",
            identified_date=date.today(), status=RiskStatus.IDENTIFIED,
            cvss_score=5.0,
            cvss_vector="AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:L/A:L",
            ssvc_decision=SSVCDecision.TRACK,
            impact_score=50, likelihood_score=50, risk_level=RiskLevel.MEDIUM,
        )
        reg.add(risk)
        assert len(reg.risks) == 1

    def test_get_risk_found(self):
        reg = RiskRegister()
        risk = Risk(
            risk_id="RSK-001", title="T", description="D",
            category=RiskCategory.DATA, owner="o",
            identified_date=date.today(), status=RiskStatus.IDENTIFIED,
            cvss_score=5.0,
            cvss_vector="AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:L/A:L",
            ssvc_decision=SSVCDecision.TRACK,
            impact_score=50, likelihood_score=50, risk_level=RiskLevel.MEDIUM,
        )
        reg.add(risk)
        assert reg.get("RSK-001") is risk
        assert reg.get("RSK-999") is None

    def test_remove_risk(self):
        reg = RiskRegister()
        risk = Risk(
            risk_id="RSK-001", title="T", description="D",
            category=RiskCategory.DATA, owner="o",
            identified_date=date.today(), status=RiskStatus.IDENTIFIED,
            cvss_score=5.0,
            cvss_vector="AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:L/A:L",
            ssvc_decision=SSVCDecision.TRACK,
            impact_score=50, likelihood_score=50, risk_level=RiskLevel.MEDIUM,
        )
        reg.add(risk)
        assert len(reg.risks) == 1
        assert reg.remove("RSK-001") is True
        assert len(reg.risks) == 0
        assert reg.remove("RSK-001") is False


class TestCVSSMetricModel:
    def test_create_cvss_metric(self):
        m = CVSSMetric(
            av=AttackVector.NETWORK, ac=AttackComplexity.LOW,
            pr=PrivilegesRequired.NONE, ui=UserInteraction.NONE,
            s=Scope.UNCHANGED, c=CIAImpact.HIGH, i=CIAImpact.HIGH, a=CIAImpact.HIGH,
        )
        assert m.av == AttackVector.NETWORK
        assert m.s == Scope.UNCHANGED


class TestSSVCMetricModel:
    def test_create_ssvc_metric(self):
        m = SSVCMetric(
            exploitation=Exploitation.ACTIVE,
            automatable=Automatable.YES,
            technical_impact=TechnicalImpact.TOTAL,
            mission_impact=MissionImpact.HIGH,
        )
        assert m.exploitation == Exploitation.ACTIVE
        assert m.mission_impact == MissionImpact.HIGH

"""Tests for SSVC v2 decision calculator."""

from src.ssvc_calc import calculate_ssvc, ssvc_to_action
from src.models import (
    Exploitation, Automatable, TechnicalImpact, MissionImpact, SSVCDecision,
)


class TestSSVCCalculator:
    def test_active_automatable_total_high(self):
        """ACTIVE + YES + TOTAL + HIGH -> ACT"""
        assert calculate_ssvc(
            Exploitation.ACTIVE, Automatable.YES,
            TechnicalImpact.TOTAL, MissionImpact.HIGH,
        ) == SSVCDecision.ACT

    def test_active_automatable_partial_medium(self):
        """ACTIVE + YES + PARTIAL + MEDIUM -> ATTEND"""
        assert calculate_ssvc(
            Exploitation.ACTIVE, Automatable.YES,
            TechnicalImpact.PARTIAL, MissionImpact.MEDIUM,
        ) == SSVCDecision.ATTEND

    def test_poc_not_automatable_partial_medium(self):
        """POC + NO + PARTIAL + MEDIUM -> ATTEND"""
        assert calculate_ssvc(
            Exploitation.POC, Automatable.NO,
            TechnicalImpact.PARTIAL, MissionImpact.MEDIUM,
        ) == SSVCDecision.TRACK_STAR

    def test_poc_not_automatable_partial_low(self):
        """POC + NO + PARTIAL + LOW -> TRACK"""
        assert calculate_ssvc(
            Exploitation.POC, Automatable.NO,
            TechnicalImpact.PARTIAL, MissionImpact.LOW,
        ) == SSVCDecision.TRACK

    def test_none_not_automatable_partial_low(self):
        """NONE + NO + PARTIAL + LOW -> TRACK"""
        assert calculate_ssvc(
            Exploitation.NONE, Automatable.NO,
            TechnicalImpact.PARTIAL, MissionImpact.LOW,
        ) == SSVCDecision.TRACK

    def test_none_automatable_total_high(self):
        """NONE + YES + TOTAL + HIGH -> ATTEND"""
        assert calculate_ssvc(
            Exploitation.NONE, Automatable.YES,
            TechnicalImpact.TOTAL, MissionImpact.HIGH,
        ) == SSVCDecision.ATTEND

    def test_all_decisions_reachable(self):
        """Verify all four decision values are reachable."""
        decisions = set()
        for exp in Exploitation:
            for auto in Automatable:
                for ti in TechnicalImpact:
                    for mi in MissionImpact:
                        decisions.add(calculate_ssvc(exp, auto, ti, mi))
        assert decisions == {
            SSVCDecision.TRACK,
            SSVCDecision.TRACK_STAR,
            SSVCDecision.ATTEND,
            SSVCDecision.ACT,
        }


class TestSSVCToAction:
    def test_act_action_message(self):
        msg = ssvc_to_action(SSVCDecision.ACT)
        assert "ACT" in msg
        assert "Immediate" in msg

    def test_track_action_message(self):
        msg = ssvc_to_action(SSVCDecision.TRACK)
        assert "TRACK" in msg
        assert "Monitor" in msg

    def test_attend_action_message(self):
        msg = ssvc_to_action(SSVCDecision.ATTEND)
        assert "ATTEND" in msg

    def test_track_star_action_message(self):
        msg = ssvc_to_action(SSVCDecision.TRACK_STAR)
        assert "TRACK*" in msg

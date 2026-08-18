"""Tests for safety checks and safe-action generation."""
from src import safety
from src.models import CaseRecord, DifferentialItem


def test_check_safety_flags_overconfident_phrases():
    assert safety.check_safety("This is definitely diagnosed as streptococcosis.")
    assert safety.check_safety("Administer antibiotics immediately.")


def test_check_safety_passes_safe_text():
    assert not safety.check_safety("Findings are not confirmed; lab testing is required.")


def test_recommended_actions_include_confirmation_and_monitoring():
    case = CaseRecord(case_id="T")
    diff = [DifferentialItem(condition_id="D02", rank=1, evidence_strength="strong", uncertainty="medium")]
    actions = safety.build_recommended_actions(case, diff)
    joined = " ".join(actions).lower()
    assert "laboratory" in joined or "confirmation" in joined
    assert "monitor" in joined


def test_escalation_for_tilv():
    diff = [DifferentialItem(condition_id="D04", rank=1, evidence_strength="strong", uncertainty="medium")]
    esc = safety.build_escalation(diff)
    assert esc
    assert "tilapia lake virus" in esc[0].lower()


def test_escalation_for_high_uncertainty_infectious():
    diff = [DifferentialItem(condition_id="D01", rank=1, evidence_strength="moderate", uncertainty="high")]
    esc = safety.build_escalation(diff)
    assert esc
    assert "professional" in esc[0].lower() or "uncertain" in esc[0].lower()


def test_no_escalation_when_confident_non_tilv():
    diff = [DifferentialItem(condition_id="D02", rank=1, evidence_strength="strong", uncertainty="low")]
    assert safety.build_escalation(diff) == []

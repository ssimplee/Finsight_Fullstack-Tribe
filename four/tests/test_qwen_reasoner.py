"""Tests for the Qwen reasoner (worksplit §5: reasoning over retrieved evidence).

The real campus API is not reachable from CI, so we mock the HTTP layer and
verify: enabled+key -> Qwen call; disabled or no key -> None (deterministic
fallback); prompt is grounded in the provided evidence.
"""
from types import SimpleNamespace

import src.qwen_reasoner as reasoner_mod
from src.models import CaseRecord, DifferentialItem, EvidenceItem, FishInfo, Observations
from src.qwen_reasoner import build_prompt, deterministic_summary, reason


def _case():
    return CaseRecord(
        case_id="T",
        fish=FishInfo(),
        observations=Observations(visual=["flank ulcer", "scale loss"], behavioral=["lethargy"]),
    )


def _evidence():
    return [
        EvidenceItem(evidence_id="KB_D02_001", condition_id="D02", label="supporting evidence",
                     text="Aeromonas may cause ulcer and scale loss."),
        EvidenceItem(evidence_id="KB_D02_004", condition_id="D02", label="conflicting evidence",
                     text="Haemorrhage overlaps with other infections."),
    ]


def _diff():
    return [DifferentialItem(condition_id="D02", rank=1, evidence_strength="strong",
                            uncertainty="medium", supporting_evidence_ids=["KB_D02_001"],
                            conflicting_evidence_ids=["KB_D02_004"], confirmation_status="unconfirmed")]


def test_disabled_returns_none(monkeypatch):
    monkeypatch.delenv("FINSIGHT_USE_QWEN_REASONER", raising=False)
    monkeypatch.delenv("QWEN_API_KEY", raising=False)
    assert reason(_case(), _evidence(), _diff(), {"D02": 4.0}) is None


def test_enabled_no_key_returns_none(monkeypatch):
    monkeypatch.setenv("FINSIGHT_USE_QWEN_REASONER", "1")
    monkeypatch.delenv("QWEN_API_KEY", raising=False)
    assert reason(_case(), _evidence(), _diff(), {"D02": 4.0}) is None


def test_enabled_no_diff_returns_none(monkeypatch):
    monkeypatch.setenv("FINSIGHT_USE_QWEN_REASONER", "1")
    monkeypatch.setenv("QWEN_API_KEY", "sk-test")
    assert reason(_case(), _evidence(), [], {}) is None


def test_enabled_calls_qwen_and_returns_text(monkeypatch):
    monkeypatch.setenv("FINSIGHT_USE_QWEN_REASONER", "1")
    monkeypatch.setenv("QWEN_API_KEY", "sk-test")
    captured = {}

    def fake_post(prompt):
        captured["prompt"] = prompt
        return "Top cause: Aeromonas. Supporting [KB_D02_001]."

    monkeypatch.setattr(reasoner_mod, "_call_qwen", fake_post)
    out = reason(_case(), _evidence(), _diff(), {"D02": 4.0})
    assert out == "Top cause: Aeromonas. Supporting [KB_D02_001]."
    # the prompt must carry the case facts + evidence IDs (grounding)
    assert "CASE:" in captured["prompt"]
    assert "KB_D02_001" in captured["prompt"]
    assert "RETRIEVED EVIDENCE" in captured["prompt"]


def test_qwen_failure_returns_none_so_caller_falls_back(monkeypatch):
    monkeypatch.setenv("FINSIGHT_USE_QWEN_REASONER", "1")
    monkeypatch.setenv("QWEN_API_KEY", "sk-test")

    def boom(prompt):
        raise RuntimeError("network down")

    monkeypatch.setattr(reasoner_mod, "_call_qwen", boom)
    assert reason(_case(), _evidence(), _diff(), {"D02": 4.0}) is None


def test_deterministic_summary_template():
    s = deterministic_summary(_diff(), "medium")
    assert "Top-ranked cause" in s
    assert "Motile Aeromonas Septicemia" in s
    assert "not confirmed" in s


def test_deterministic_summary_empty_diff():
    s = deterministic_summary([], "high")
    assert "insufficient" in s.lower()

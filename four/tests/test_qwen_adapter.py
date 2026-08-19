"""Tests for the RealQwenAdapter bridging Member 3 -> Member 4 vision contract.

Uses stub objects shaped like Member 3's VisionResult / VisionFinding so the
adapter logic is verified without a live Qwen call or Member 3's modules.
"""
from types import SimpleNamespace

from src.qwen_client import (
    ImageObservation,
    MockQwenClient,
    RealQwenAdapter,
    _vision_result_to_observation,
)


def _result(quality="usable", quality_reason="", findings=None):
    return SimpleNamespace(
        quality=quality,
        quality_reason=quality_reason,
        findings=findings or [],
        metrics=None,
    )


def _finding(text, region=None, modality="image"):
    return SimpleNamespace(finding=text, region=region, modality=modality)


def test_usable_result_maps_to_quality_ok():
    r = _result("usable", "ok", [_finding("flank ulcer"), _finding("scale loss")])
    obs = _vision_result_to_observation(r)
    assert obs.quality_ok is True
    assert obs.visual == ["flank ulcer", "scale loss"]
    assert obs.behavioral == []


def test_behavioral_finding_routed_to_behavioral():
    r = _result("usable", "", [_finding("surface gasping"), _finding("flank ulcer")])
    obs = _vision_result_to_observation(r)
    assert "surface gasping" in obs.behavioral
    assert "flank ulcer" in obs.visual
    # behavioural keyword must not also leak into visual
    assert "surface gasping" not in obs.visual


def test_poor_quality_marks_not_ok_and_keeps_reason():
    r = _result("poor_quality", "image too blurry")
    obs = _vision_result_to_observation(r)
    assert obs.quality_ok is False
    assert "blurry" in obs.note
    assert obs.visual == []  # no findings -> nothing fabricated


def test_empty_findings_never_fabricates_a_diagnosis():
    r = _result("usable", "", [])
    obs = _vision_result_to_observation(r)
    assert obs.visual == []
    assert obs.behavioral == []
    assert obs.quality_ok is True


def test_adapter_falls_back_when_member3_module_missing(monkeypatch):
    # Force the lazy import of Member 3's module to fail -> mock fallback.
    import sys
    monkeypatch.setitem(sys.modules, "app.services.vision_analysis", None)
    adapter = RealQwenAdapter(api_key="", base_url="", model="")
    obs = adapter.analyze_image("tilapia_flank_ulcer.jpg")
    # MockQwenClient returns canned findings for that filename.
    assert "flank ulcer" in obs.visual
    assert obs.quality_ok is True


def test_adapter_falls_back_on_qwen_failure(monkeypatch):
    # Member 3 module importable, but client.analyze_image raises -> fallback.
    import sys, types
    fake_mod = types.ModuleType("app.services.vision_analysis")
    monkeypatch.setitem(sys.modules, "app.services.vision_analysis", fake_mod)

    class _BoomClient:
        def analyze_image(self, image):
            raise RuntimeError("network down")

    adapter = RealQwenAdapter(api_key="x", base_url="x", model="x")
    adapter._client = _BoomClient()  # pre-bake so _build_real_client is skipped
    obs = adapter.analyze_image("tilapia_pop_eye.jpg")
    assert "exophthalmia" in obs.visual  # from MockQwenClient canned set

"""Tests for vision analysis orchestration (Member 3) -- fully mocked."""

from __future__ import annotations

import json

import pytest

from app.services import vision_analysis as va
from app.services.qwen_client import QwenClient, QwenParseError
from app.services.vision_analysis import (
    analyze_image,
    check_image_quality,
    filter_diagnostic_findings,
    is_diagnostic,
    precheck_image,
)
from app.services.vision_prompts import build_quality_prompt, build_vision_prompt
from app.services.vision_schemas import ImageQuality, VisionFinding, VisionResult

# A minimal valid PNG header (20x20) that passes the local precheck.
VALID_PNG = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x14\x00\x00\x00\x14"


@pytest.fixture(autouse=True)
def _clear_vision_cache():
    va._vision_cache.clear()
    yield
    va._vision_cache.clear()


# ------------------------------------------------------- diagnostic filtering


class TestDiagnosticFilter:
    def test_pure_observation_kept(self):
        assert not is_diagnostic("red ulcer on flank")
        assert not is_diagnostic("bulging left eye")
        assert not is_diagnostic("fin erosion on dorsal fin")

    def test_diagnostic_language_detected(self):
        assert is_diagnostic("consistent with Aeromonas infection")
        assert is_diagnostic("diagnosis: streptococcosis")
        assert is_diagnostic("caused by poor water quality")
        assert is_diagnostic("needs antibiotic treatment")
        assert is_diagnostic("疑似细菌感染")

    def test_filter_drops_diagnostic_findings(self):
        findings = [
            VisionFinding(finding="red ulcer on flank", region="flank"),
            VisionFinding(finding="likely bacterial infection", region="whole body"),
            VisionFinding(finding="exophthalmia", region="eye"),
            VisionFinding(finding="recommend antibiotic treatment", region=None),
        ]
        kept = filter_diagnostic_findings(findings)
        assert [f.finding for f in kept] == ["red ulcer on flank", "exophthalmia"]


# -------------------------------------------------------------------- prompts


class TestPrompts:
    def test_vision_prompt_requests_json_and_visible_only(self):
        prompt = build_vision_prompt()
        assert "JSON" in prompt
        assert "visible" in prompt
        # The prompt must explicitly forbid diagnostic output.
        assert "Do NOT include disease names" in prompt

    def test_vision_prompt_never_asks_for_a_disease_name(self):
        prompt = build_vision_prompt().lower()
        assert "what disease" not in prompt
        assert "which disease" not in prompt

    def test_quality_prompt_returns_two_fields(self):
        prompt = build_quality_prompt()
        assert '"quality"' in prompt
        assert '"quality_reason"' in prompt


# ------------------------------------------------------------- quality checks


class TestCheckImageQuality:
    def test_returns_quality_and_reason(self, monkeypatch):
        client = QwenClient(api_key="k")

        def fake_chat(messages, max_tokens=1024):
            return json.dumps(
                {"quality": "no_relevant_subject", "quality_reason": "no fish in image"}
            )

        monkeypatch.setattr(client, "chat", fake_chat)
        quality, reason = check_image_quality(b"\x89PNG fake", client=client)
        assert quality is ImageQuality.NO_RELEVANT_SUBJECT
        assert reason == "no fish in image"


# --------------------------------------------------------------- main pipeline


class TestAnalyzeImagePipeline:
    def _client_returning(self, monkeypatch, result: VisionResult) -> QwenClient:
        client = QwenClient(api_key="k")
        monkeypatch.setattr(client, "analyze_image", lambda image, prompt=None, max_tokens=1024: result)
        return client

    def test_usable_image_keeps_filtered_findings(self, monkeypatch):
        raw = VisionResult(
            quality=ImageQuality.USABLE,
            quality_reason="fish clearly visible",
            findings=[
                VisionFinding(finding="red ulcer on flank", region="flank"),
                VisionFinding(finding="signs of streptococcosis", region="whole body"),
            ],
        )
        client = self._client_returning(monkeypatch, raw)
        out = analyze_image(b"\x89PNG fake", client=client)
        assert out.quality is ImageQuality.USABLE
        assert [f.finding for f in out.findings] == ["red ulcer on flank"]

    def test_poor_quality_image_never_returns_findings(self, monkeypatch):
        # Even if the model violated the rules and produced findings.
        raw = VisionResult(
            quality=ImageQuality.POOR_QUALITY,
            quality_reason="image too blurry",
            findings=[VisionFinding(finding="red ulcer on flank")],
        )
        client = self._client_returning(monkeypatch, raw)
        out = analyze_image(b"\x89PNG fake", client=client)
        assert out.quality is ImageQuality.POOR_QUALITY
        assert out.quality_reason == "image too blurry"
        assert out.findings == []

    def test_no_relevant_subject_image_never_returns_findings(self, monkeypatch):
        raw = VisionResult(
            quality=ImageQuality.NO_RELEVANT_SUBJECT,
            quality_reason="image shows a bucket, no fish",
            findings=[VisionFinding(finding="something")],
        )
        client = self._client_returning(monkeypatch, raw)
        out = analyze_image(b"\x89PNG fake", client=client)
        assert out.quality is ImageQuality.NO_RELEVANT_SUBJECT
        assert out.findings == []


# ----------------------------------------------------------------- local precheck


class TestPrecheck:
    def test_empty_bytes_blocked(self):
        quality, _ = precheck_image(b"")
        assert quality is ImageQuality.POOR_QUALITY

    def test_non_image_blocked(self):
        quality, _ = precheck_image(b"definitely not an image")
        assert quality is ImageQuality.NO_RELEVANT_SUBJECT

    def test_tiny_image_blocked(self):
        tiny = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        quality, reason = precheck_image(tiny)
        assert quality is ImageQuality.POOR_QUALITY
        assert "too small" in reason

    def test_valid_image_passes(self):
        assert precheck_image(VALID_PNG) is None

    def test_url_passthrough(self):
        assert precheck_image("https://example.com/fish.jpg") is None


# ------------------------------------------------------------------------ cache


class TestCache:
    def test_same_image_analyzed_once(self, monkeypatch):
        client = QwenClient(api_key="k")
        calls = {"n": 0}

        def fake_analyze(image, prompt=None, max_tokens=1024):
            calls["n"] += 1
            return VisionResult(
                quality=ImageQuality.USABLE,
                quality_reason="ok",
                findings=[VisionFinding(finding="red ulcer on flank")],
            )

        monkeypatch.setattr(client, "analyze_image", fake_analyze)
        analyze_image(VALID_PNG, client=client)
        analyze_image(VALID_PNG, client=client)
        assert calls["n"] == 1


# --------------------------------------------------------------- parse fallback


class TestParseFallback:
    def test_parse_error_falls_back_to_quality_only(self, monkeypatch):
        client = QwenClient(api_key="k")

        def fail_analyze(image, prompt=None, max_tokens=1024):
            raise QwenParseError("no json found")

        monkeypatch.setattr(client, "analyze_image", fail_analyze)
        monkeypatch.setattr(
            va,
            "check_image_quality",
            lambda image, client=None: (ImageQuality.POOR_QUALITY, "could not parse"),
        )
        out = analyze_image(VALID_PNG, client=client)
        assert out.quality is ImageQuality.POOR_QUALITY
        assert out.findings == []


# ---------------------------------------------------------------------- metrics


class TestMetrics:
    def test_metrics_attached(self, monkeypatch):
        client = QwenClient(api_key="k")
        client.last_total_tokens = 42
        client.last_retry_count = 1

        monkeypatch.setattr(
            client,
            "analyze_image",
            lambda image, prompt=None, max_tokens=1024: VisionResult(
                quality=ImageQuality.USABLE,
                quality_reason="ok",
                findings=[VisionFinding(finding="red ulcer on flank")],
            ),
        )
        out = analyze_image(VALID_PNG, client=client)
        assert out.metrics is not None
        assert out.metrics["model"] == client.model
        assert out.metrics["total_tokens"] == 42
        assert out.metrics["retry_count"] == 1
        assert out.metrics["quality"] == "usable"
        assert out.metrics["input_hash"] is not None
        assert "latency_ms" in out.metrics
        assert "timestamp" in out.metrics


# ----------------------------------------------------------------- cache LRU


class TestVisionCacheLRU:
    def test_eviction_and_limit(self):
        from app.services.vision_cache import VisionCache

        cache = VisionCache(max_size=2)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)  # evicts oldest "a"
        assert cache.get("a") is None
        assert cache.get("b") == 2
        assert cache.get("c") == 3
        assert len(cache) == 2

    def test_get_refreshes_recency(self):
        from app.services.vision_cache import VisionCache

        cache = VisionCache(max_size=2)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.get("a")  # make "a" most-recently-used
        cache.set("c", 3)  # evicts "b"
        assert cache.get("a") == 1
        assert cache.get("b") is None
        assert cache.get("c") == 3

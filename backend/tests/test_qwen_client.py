"""Tests for QwenClient (Member 3) -- fully mocked, no network required."""

from __future__ import annotations

import json

import httpx
import pytest

from app.services import qwen_client as qc
from app.services.qwen_client import (
    QwenAPIError,
    QwenClient,
    QwenConfigError,
    QwenParseError,
    image_to_data_url,
    parse_vision_reply,
)
from app.services.vision_schemas import ImageQuality

PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
)


def _ok_response(content: str) -> dict:
    return {"choices": [{"message": {"role": "assistant", "content": content}}]}


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch):
    # Keep retry-backoff tests instant.
    monkeypatch.setattr(qc.time, "sleep", lambda *_: None)


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    monkeypatch.delenv("QWEN_API_KEY", raising=False)
    monkeypatch.delenv("QWEN_MODEL", raising=False)
    monkeypatch.delenv("QWEN_BASE_URL", raising=False)
    monkeypatch.delenv("QWEN_VERIFY_SSL", raising=False)


# --------------------------------------------------------------------- config


class TestConfig:
    def test_init_without_api_key_does_not_raise(self):
        QwenClient(api_key="")

    def test_missing_api_key_raises_on_call(self):
        client = QwenClient(api_key="")
        with pytest.raises(QwenConfigError):
            client.chat([{"role": "user", "content": "hi"}])

    def test_default_endpoint_matches_campus_platform(self):
        client = QwenClient(api_key="k")
        assert client.base_url == "https://model.ai.szu.edu.cn/v1"
        assert client.model == "qwen3-vl-8b"


# ----------------------------------------------------------------------- chat


class TestChat:
    def test_chat_returns_assistant_text(self, monkeypatch):
        client = QwenClient(api_key="k")
        monkeypatch.setattr(client, "_request_with_retries", lambda payload: _ok_response("hello"))
        assert client.chat([{"role": "user", "content": "hi"}]) == "hello"

    def test_chat_raises_on_unexpected_shape(self, monkeypatch):
        client = QwenClient(api_key="k")
        monkeypatch.setattr(client, "_request_with_retries", lambda payload: {"unexpected": True})
        with pytest.raises(QwenParseError):
            client.chat([{"role": "user", "content": "hi"}])

    def test_chat_passes_response_format(self, monkeypatch):
        client = QwenClient(api_key="k")
        captured: dict = {}

        def fake_request(payload):
            captured.update(payload)
            return _ok_response("ok")

        monkeypatch.setattr(client, "_request_with_retries", fake_request)
        client.chat(
            [{"role": "user", "content": "hi"}],
            response_format={"type": "json_object"},
        )
        assert captured["response_format"] == {"type": "json_object"}


# --------------------------------------------------------------------- retries


class TestRetries:
    def test_retries_then_succeeds(self, monkeypatch):
        client = QwenClient(api_key="k", max_retries=2)
        calls = {"n": 0}

        def flaky(url, headers, payload):
            calls["n"] += 1
            if calls["n"] < 3:
                raise qc._RetryableError("timeout")
            return _ok_response("ok")

        monkeypatch.setattr(client, "_request_once", flaky)
        assert client.chat([{"role": "user", "content": "hi"}]) == "ok"
        assert calls["n"] == 3

    def test_retries_exhausted_raises_api_error(self, monkeypatch):
        client = QwenClient(api_key="k", max_retries=1)

        def always_fail(url, headers, payload):
            raise qc._RetryableError("boom")

        monkeypatch.setattr(client, "_request_once", always_fail)
        with pytest.raises(QwenAPIError):
            client.chat([{"role": "user", "content": "hi"}])

    def test_auth_error_fails_fast_without_retry(self, monkeypatch):
        calls = {"n": 0}

        def handler(request):
            calls["n"] += 1
            return httpx.Response(401, json={"error": "unauthorized"})

        client = QwenClient(api_key="bad-key", max_retries=3)
        monkeypatch.setattr(client, "_http", httpx.Client(transport=httpx.MockTransport(handler)))
        with pytest.raises(QwenAPIError, match="401"):
            client.chat([{"role": "user", "content": "hi"}])
        assert calls["n"] == 1

    def test_server_error_is_retried(self, monkeypatch):
        calls = {"n": 0}

        def handler(request):
            calls["n"] += 1
            return httpx.Response(503, json={"error": "overloaded"})

        client = QwenClient(api_key="k", max_retries=2)
        monkeypatch.setattr(client, "_http", httpx.Client(transport=httpx.MockTransport(handler)))
        with pytest.raises(QwenAPIError):
            client.chat([{"role": "user", "content": "hi"}])
        assert calls["n"] == 3  # 1 initial + 2 retries


# ------------------------------------------------------------- image handling


class TestImageToDataUrl:
    def test_png_bytes_detected(self):
        url = image_to_data_url(PNG_BYTES)
        assert url.startswith("data:image/png;base64,")

    def test_existing_data_url_passthrough(self):
        assert image_to_data_url("data:image/jpeg;base64,AAA") == "data:image/jpeg;base64,AAA"

    def test_http_url_passthrough(self):
        assert image_to_data_url("https://example.com/fish.jpg") == "https://example.com/fish.jpg"

    def test_missing_file_raises(self):
        with pytest.raises(FileNotFoundError):
            image_to_data_url("c:/definitely/not/a/real/image.png")

    def test_fixture_file_loads(self):
        from pathlib import Path

        fixture = Path(__file__).parent / "fixtures" / "sample_placeholder.png"
        assert image_to_data_url(str(fixture)).startswith("data:image/png;base64,")


# ---------------------------------------------------------------- vision call


class TestAnalyzeImage:
    def test_builds_multimodal_messages_and_parses_reply(self, monkeypatch):
        client = QwenClient(api_key="k")
        captured: dict = {}

        def fake_chat(messages, max_tokens=1024, response_format=None):
            captured["messages"] = messages
            captured["response_format"] = response_format
            return json.dumps(
                {
                    "quality": "usable",
                    "quality_reason": "fish clearly visible",
                    "findings": [{"finding": "red ulcer on flank", "region": "flank"}],
                }
            )

        monkeypatch.setattr(client, "chat", fake_chat)
        result = client.analyze_image(PNG_BYTES)

        assert result.quality is ImageQuality.USABLE
        assert result.findings[0].finding == "red ulcer on flank"
        assert result.findings[0].modality == "image"

        system, user = captured["messages"][0], captured["messages"][1]
        assert "never diagnose" in system["content"]
        part_types = [part["type"] for part in user["content"]]
        assert part_types == ["text", "image_url"]
        assert user["content"][1]["image_url"]["url"].startswith("data:image/png;base64,")
        assert captured["response_format"] == {"type": "json_object"}

    def test_analyze_image_falls_back_on_parse_error(self, monkeypatch):
        client = QwenClient(api_key="k")
        calls: list = []

        def fake_chat(messages, max_tokens=1024, response_format=None):
            calls.append(response_format)
            if response_format is not None:
                return "not json at all"
            return json.dumps({"quality": "usable", "quality_reason": "ok", "findings": []})

        monkeypatch.setattr(client, "chat", fake_chat)
        result = client.analyze_image(PNG_BYTES)
        assert result.quality is ImageQuality.USABLE
        assert calls == [{"type": "json_object"}, None]

    def test_analyze_image_falls_back_on_api_error(self, monkeypatch):
        client = QwenClient(api_key="k")
        calls: list = []

        def fake_chat(messages, max_tokens=1024, response_format=None):
            calls.append(response_format)
            if response_format is not None:
                raise QwenAPIError("HTTP 400: response_format not supported")
            return json.dumps({"quality": "usable", "quality_reason": "ok", "findings": []})

        monkeypatch.setattr(client, "chat", fake_chat)
        result = client.analyze_image(PNG_BYTES)
        assert result.quality is ImageQuality.USABLE
        assert calls == [{"type": "json_object"}, None]


# --------------------------------------------------------------- reply parser


class TestParseVisionReply:
    def test_plain_json(self):
        text = '{"quality": "usable", "quality_reason": "ok", "findings": [{"finding": "fin erosion"}]}'
        result = parse_vision_reply(text)
        assert result.quality is ImageQuality.USABLE
        assert [f.finding for f in result.findings] == ["fin erosion"]

    def test_markdown_fenced_json(self):
        text = 'Here is the result:\n```json\n{"quality": "poor_quality", "quality_reason": "blurry", "findings": []}\n```'
        result = parse_vision_reply(text)
        assert result.quality is ImageQuality.POOR_QUALITY
        assert result.findings == []

    def test_unknown_quality_falls_back_to_poor(self):
        result = parse_vision_reply('{"quality": "whatever", "findings": []}')
        assert result.quality is ImageQuality.POOR_QUALITY

    def test_no_json_raises(self):
        with pytest.raises(QwenParseError):
            parse_vision_reply("sorry, I cannot answer")

    def test_malformed_json_raises(self):
        with pytest.raises(QwenParseError):
            parse_vision_reply("{'quality': broken}")

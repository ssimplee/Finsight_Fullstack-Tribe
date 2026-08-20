"""Qwen multimodal client for FinSight (Member 3).

Talks to any OpenAI-compatible /v1/chat/completions endpoint.
Default deployment: campus AI platform (model.ai.szu.edu.cn) running
qwen3-vl-8b, see FinSight/智算中心大模型调用方法.docx.

Design rules:
- returns observations, never a diagnosis;
- timeout + bounded retries with backoff for transient errors;
- readable errors for config/auth/parse failures.
"""

from __future__ import annotations

import base64
import json
import os
import re
import time
from pathlib import Path

import httpx

from app.services.vision_prompts import VISION_SYSTEM_PROMPT, build_vision_prompt
from app.services.vision_schemas import ImageQuality, VisionFinding, VisionResult

DEFAULT_BASE_URL = "https://model.ai.szu.edu.cn/v1"
DEFAULT_MODEL = "qwen3-vl-8b"
DEFAULT_TIMEOUT_SEC = 60.0
DEFAULT_MAX_RETRIES = 3
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


class QwenConfigError(RuntimeError):
    """Raised when required Qwen settings are missing."""


class QwenAPIError(RuntimeError):
    """Raised when the vision endpoint fails (non-retryable or after retries)."""


class QwenParseError(RuntimeError):
    """Raised when the model reply cannot be parsed as structured output."""


class _RetryableError(Exception):
    """Internal marker for transient failures worth retrying."""


def _detect_mime(data: bytes) -> str:
    """Sniff common image magic bytes; default to jpeg."""
    if data.startswith(b"\x89PNG"):
        return "image/png"
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"GIF8"):
        return "image/gif"
    if data.startswith(b"BM"):
        return "image/bmp"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return "image/jpeg"


def image_to_data_url(image: str | bytes, mime: str | None = None) -> str:
    """Accept a local path, raw bytes, data URL or http(s) URL; return a data URL."""
    if isinstance(image, str) and image.startswith(("data:", "http://", "https://")):
        return image
    if isinstance(image, (bytes, bytearray)):
        data = bytes(image)
    else:
        path = Path(image)
        if not path.is_file():
            raise FileNotFoundError(f"Image not found: {image}")
        data = path.read_bytes()
    detected = mime or _detect_mime(data)
    encoded = base64.b64encode(data).decode("ascii")
    return f"data:{detected};base64,{encoded}"


_JSON_BLOCK_RE = re.compile(r"\{.*\}", re.DOTALL)


def parse_vision_reply(text: str) -> VisionResult:
    """Parse the model reply into VisionResult; tolerate markdown code fences."""
    match = _JSON_BLOCK_RE.search(text)
    if not match:
        raise QwenParseError(f"No JSON object found in model reply: {text[:200]!r}")
    try:
        raw = json.loads(match.group(0))
    except json.JSONDecodeError as exc:
        raise QwenParseError(f"Malformed JSON in model reply: {text[:200]!r}") from exc

    quality_raw = str(raw.get("quality", ImageQuality.POOR_QUALITY.value)).strip().lower()
    try:
        quality = ImageQuality(quality_raw)
    except ValueError:
        quality = ImageQuality.POOR_QUALITY

    findings: list[VisionFinding] = []
    for item in raw.get("findings") or []:
        if not isinstance(item, dict):
            continue
        finding_text = str(item.get("finding", "")).strip()
        if not finding_text:
            continue
        region = item.get("region")
        findings.append(VisionFinding(finding=finding_text, region=str(region) if region else None))
    return VisionResult(
        quality=quality,
        quality_reason=str(raw.get("quality_reason", "")),
        findings=findings,
    )


class QwenClient:
    """Thin OpenAI-compatible client with timeout, retries and readable errors."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        timeout_sec: float | None = None,
        max_retries: int | None = None,
        verify_ssl: bool | None = None,
    ) -> None:
        self.api_key = api_key if api_key is not None else os.getenv("QWEN_API_KEY", "")
        self.model = model or os.getenv("QWEN_MODEL", DEFAULT_MODEL)
        self.base_url = (base_url or os.getenv("QWEN_BASE_URL", DEFAULT_BASE_URL)).rstrip("/")
        self.timeout_sec = timeout_sec if timeout_sec is not None else float(
            os.getenv("QWEN_TIMEOUT_SEC", DEFAULT_TIMEOUT_SEC)
        )
        self.max_retries = max_retries if max_retries is not None else int(
            os.getenv("QWEN_MAX_RETRIES", DEFAULT_MAX_RETRIES)
        )
        if verify_ssl is None:
            verify_ssl = os.getenv("QWEN_VERIFY_SSL", "true").strip().lower() != "false"
        self.verify_ssl = verify_ssl
        self._http: httpx.Client | None = None
        # Last-request metrics exposed to the observability layer.
        self.last_total_tokens: int | None = None
        self.last_retry_count: int = 0

    # ------------------------------------------------------------------ low level

    def _client(self) -> httpx.Client:
        if self._http is None:
            self._http = httpx.Client(timeout=self.timeout_sec, verify=self.verify_ssl)
        return self._http

    def _require_api_key(self) -> None:
        if not self.api_key:
            raise QwenConfigError(
                "QWEN_API_KEY is not configured. Set it in the environment "
                "(see backend/.env.example and the campus platform guide)."
            )

    def _request_once(self, url: str, headers: dict, payload: dict) -> dict:
        try:
            resp = self._client().post(url, headers=headers, json=payload)
        except (httpx.TimeoutException, httpx.TransportError) as exc:
            raise _RetryableError(str(exc)) from exc
        if resp.status_code in RETRYABLE_STATUS_CODES:
            raise _RetryableError(f"HTTP {resp.status_code}: {resp.text[:200]}")
        if resp.status_code >= 400:
            # Non-retryable client errors (auth, bad request...): fail fast.
            raise QwenAPIError(f"HTTP {resp.status_code}: {resp.text[:300]}")
        data = resp.json()
        usage = data.get("usage") or {}
        self.last_total_tokens = usage.get("total_tokens")
        return data

    def _request_with_retries(self, payload: dict) -> dict:
        url = f"{self.base_url}/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            self.last_retry_count = attempt
            if attempt:
                time.sleep(min(0.5 * (2 ** (attempt - 1)), 8.0))
            try:
                return self._request_once(url, headers, payload)
            except _RetryableError as exc:
                last_error = exc
        raise QwenAPIError(
            f"Qwen request failed after {self.max_retries + 1} attempts: {last_error}"
        ) from last_error

    # -------------------------------------------------------------------- chat

    def chat(
        self,
        messages: list[dict],
        max_tokens: int = 1024,
        response_format: dict | None = None,
    ) -> str:
        """Send one chat/completions request and return the assistant text."""
        self._require_api_key()
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "max_tokens": max_tokens,
        }
        if response_format is not None:
            payload["response_format"] = response_format
        data = self._request_with_retries(payload)
        try:
            return data["choices"][0]["message"]["content"] or ""
        except (KeyError, IndexError, TypeError) as exc:
            raise QwenParseError(f"Unexpected chat response shape: {str(data)[:200]}") from exc

    # ------------------------------------------------------------------ vision

    def analyze_image(
        self,
        image: str | bytes,
        prompt: str | None = None,
        max_tokens: int = 1024,
    ) -> VisionResult:
        """Analyze one image and return structured observations (never a diagnosis)."""
        data_url = image_to_data_url(image)
        messages = [
            {"role": "system", "content": VISION_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt or build_vision_prompt()},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            },
        ]
        try:
            text = self.chat(
                messages,
                max_tokens=max_tokens,
                response_format={"type": "json_object"},
            )
            return parse_vision_reply(text)
        except (QwenAPIError, QwenParseError):
            # Some OpenAI-compatible servers reject response_format, and small
            # models sometimes ignore it. Retry once in plain-text mode.
            text = self.chat(messages, max_tokens=max_tokens)
            return parse_vision_reply(text)

"""Orchestration for visual analysis (Member 3).

Pipeline: local precheck -> cache -> Qwen call -> quality gate -> diagnostic filter.
- local precheck: block obviously invalid images before spending tokens;
- cache: avoid duplicate API calls for identical images;
- metrics: emit latency/token/retry observability per call.
"""

from __future__ import annotations

import hashlib
import re
import time
from pathlib import Path

from app.services.qwen_client import (
    QwenClient,
    QwenParseError,
    image_to_data_url,
    parse_vision_reply,
)
from app.services.vision_cache import VisionCache
from app.services.vision_metrics import VisionMetrics, utc_now_iso
from app.services.vision_prompts import build_quality_prompt, build_vision_prompt
from app.services.vision_schemas import ImageQuality, VisionFinding, VisionResult

_MIN_DIMENSION = 16

# Words that turn an observation into a diagnosis / cause / treatment claim.
_DIAGNOSTIC_PATTERNS = [
    r"diagnos",
    r"infecti",
    r"disease",
    r"pathogen",
    r"bacteri",
    r"viral",
    r"virus",
    r"streptococc",
    r"aeromonas",
    r"columnaris",
    r"tilv",
    r"septic",
    r"caused by",
    r"due to",
    r"confirm",
    r"treat",
    r"medicat",
    r"antibiotic",
    r"therapy",
    r"确诊",
    r"诊断",
    r"感染",
    r"疾病",
    r"病原",
    r"治疗",
    r"用药",
]
_DIAGNOSTIC_RE = re.compile("|".join(_DIAGNOSTIC_PATTERNS), re.IGNORECASE)

_vision_cache = VisionCache()


def is_diagnostic(text: str) -> bool:
    """True when the text reads like a diagnosis/cause/treatment claim."""
    return bool(_DIAGNOSTIC_RE.search(text))


def filter_diagnostic_findings(findings: list[VisionFinding]) -> list[VisionFinding]:
    """Drop findings containing diagnostic language; keep pure observations."""
    return [f for f in findings if not is_diagnostic(f.finding)]


# ------------------------------------------------------------------ local precheck


def _sniff_image_type(data: bytes) -> str | None:
    """Return a known image kind from magic bytes, or None if unrecognized."""
    if data.startswith(b"\x89PNG"):
        return "png"
    if data.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if data.startswith((b"GIF87a", b"GIF89a")):
        return "gif"
    if data.startswith(b"BM"):
        return "bmp"
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    return None


def _jpeg_dimensions(data: bytes) -> tuple[int, int] | None:
    """Scan JPEG markers for a SOF segment and read width/height."""
    n = len(data)
    i = 2
    while i + 4 <= n:
        if data[i] != 0xFF:
            i += 1
            continue
        while i < n and data[i] == 0xFF:
            i += 1
        if i >= n:
            break
        marker = data[i]
        i += 1
        if marker in (0xC0, 0xC2):  # SOF0 / SOF2
            if i + 7 <= n:
                height = int.from_bytes(data[i + 3 : i + 5], "big")
                width = int.from_bytes(data[i + 5 : i + 7], "big")
                return width, height
            break
        if marker in (0xD8, 0xD9):  # SOI / EOI (no payload)
            continue
        if marker == 0xDA:  # SOS: scan data follows, stop
            break
        if i + 2 > n:
            break
        seg_len = int.from_bytes(data[i : i + 2], "big")
        i += seg_len
    return None


def _image_dimensions(data: bytes, kind: str) -> tuple[int, int] | None:
    if kind == "png" and len(data) >= 24:
        return int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")
    if kind == "gif" and len(data) >= 10:
        return int.from_bytes(data[6:8], "little"), int.from_bytes(data[8:10], "little")
    if kind == "bmp" and len(data) >= 26:
        return int.from_bytes(data[18:22], "little"), int.from_bytes(data[22:26], "little")
    if kind == "jpeg":
        return _jpeg_dimensions(data)
    return None


def precheck_image(image: str | bytes) -> tuple[ImageQuality, str] | None:
    """Return (quality, reason) to short-circuit, or None to continue to the model.

    Only blocks images that can be judged locally with confidence; external URLs
    are passed through to the model untouched.
    """
    if isinstance(image, str):
        if image.startswith(("data:", "http://", "https://")):
            return None
        try:
            data = Path(image).read_bytes()
        except OSError:
            return (ImageQuality.NO_RELEVANT_SUBJECT, "image file not found")
    else:
        data = bytes(image)

    if not data:
        return (ImageQuality.POOR_QUALITY, "empty image data")

    kind = _sniff_image_type(data)
    if kind is None:
        return (ImageQuality.NO_RELEVANT_SUBJECT, "not a recognized image format")

    dims = _image_dimensions(data, kind)
    if dims is not None and (dims[0] < _MIN_DIMENSION or dims[1] < _MIN_DIMENSION):
        return (ImageQuality.POOR_QUALITY, "image too small to inspect")

    return None


# ------------------------------------------------------------------ caching


def _content_bytes(image: str | bytes) -> bytes | None:
    if isinstance(image, (bytes, bytearray)):
        return bytes(image)
    if isinstance(image, str):
        if image.startswith(("data:", "http://", "https://")):
            return image.encode("utf-8")
        try:
            return Path(image).read_bytes()
        except OSError:
            return None
    return None


def _cache_key(image: str | bytes) -> str | None:
    data = _content_bytes(image)
    if data is None:
        return None
    return hashlib.sha256(data).hexdigest()


# ------------------------------------------------------------------ metrics


def _attach_metrics(
    result: VisionResult,
    client: QwenClient,
    started: float,
    key: str | None,
) -> VisionResult:
    metrics = VisionMetrics(
        model=client.model,
        latency_ms=int((time.perf_counter() - started) * 1000),
        total_tokens=client.last_total_tokens,
        retry_count=client.last_retry_count,
        input_hash=key,
        quality=result.quality.value,
        timestamp=utc_now_iso(),
    )
    result.metrics = metrics.model_dump()
    return result


# ------------------------------------------------------------------ orchestration


def check_image_quality(
    image: str | bytes,
    client: QwenClient | None = None,
) -> tuple[ImageQuality, str]:
    """Standalone lightweight quality check (separate API call)."""
    client = client or QwenClient()
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": build_quality_prompt()},
                {"type": "image_url", "image_url": {"url": image_to_data_url(image)}},
            ],
        }
    ]
    text = client.chat(messages, max_tokens=256)
    result = parse_vision_reply(text)
    return result.quality, result.quality_reason


def _quality_only_fallback(image: str | bytes, client: QwenClient) -> VisionResult:
    """Recover from a parse failure with a minimal quality-only prompt."""
    try:
        quality, reason = check_image_quality(image, client=client)
    except QwenParseError:
        quality, reason = ImageQuality.POOR_QUALITY, "could not parse model output"
    return VisionResult(quality=quality, quality_reason=reason, findings=[])


def analyze_image(
    image: str | bytes,
    client: QwenClient | None = None,
) -> VisionResult:
    """Full pipeline: precheck -> cache -> Qwen -> quality gate -> diagnostic filter."""
    client = client or QwenClient()
    started = time.perf_counter()

    pre = precheck_image(image)
    if pre is not None:
        quality, reason = pre
        return _attach_metrics(
            VisionResult(quality=quality, quality_reason=reason, findings=[]),
            client,
            started,
            None,
        )

    key = _cache_key(image)
    if key is not None:
        cached = _vision_cache.get(key)
        if cached is not None:
            return cached

    try:
        result = client.analyze_image(image, prompt=build_vision_prompt())
    except QwenParseError:
        result = _quality_only_fallback(image, client)

    if result.quality != ImageQuality.USABLE:
        final = VisionResult(
            quality=result.quality,
            quality_reason=result.quality_reason,
            findings=[],
        )
    else:
        final = VisionResult(
            quality=ImageQuality.USABLE,
            quality_reason=result.quality_reason,
            findings=filter_diagnostic_findings(result.findings),
        )

    final = _attach_metrics(final, client, started, key)

    if key is not None:
        _vision_cache.set(key, final)

    return final
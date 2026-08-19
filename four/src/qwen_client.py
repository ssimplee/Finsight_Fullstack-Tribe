"""Qwen multimodal image-analysis interface (Member 3 -> Member 4 contract).

Member 3 implements `QwenClient.analyze_image` against the real Qwen API.
Member 4 consumes the result as `ImageObservation`. A `MockQwenClient` is
provided so the full image -> observation -> RAG -> differential chain can run
without a live Qwen call.

Key rule (from worksplit §5): Qwen returns *observations*, NOT a diagnosis.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass
class ImageObservation:
    """Structured output of one Qwen image analysis.

    Fields:
        visual: visible findings on the fish, e.g. ["flank ulcer", "scale loss"].
        behavioral: behavior visible in the image, e.g. ["lethargy"].
        quality_ok: whether the image was clear enough to analyze.
        note: optional quality / rejection note.
    """

    visual: list[str] = field(default_factory=list)
    behavioral: list[str] = field(default_factory=list)
    quality_ok: bool = True
    note: str = ""


class QwenClient:
    """Protocol Member 3 implements. Returns observations, NOT a diagnosis."""

    def analyze_image(self, image_path: str) -> ImageObservation:
        raise NotImplementedError


# Canned observations keyed by filename, for offline development.
DEFAULT_CANNED: dict[str, ImageObservation] = {
    "tilapia_flank_ulcer.jpg": ImageObservation(
        visual=["flank ulcer", "scale loss", "hemorrhagic fin"],
        behavioral=["lethargy"],
    ),
    "tilapia_pop_eye.jpg": ImageObservation(
        visual=["exophthalmia", "corneal opacity"],
        behavioral=[],
    ),
    "tilapia_gasping.jpg": ImageObservation(
        visual=[],
        behavioral=["surface gasping", "rapid gill movement"],
    ),
    "tilapia_dark_hemorrhage.jpg": ImageObservation(
        visual=["darkening", "body hemorrhage", "pale gill"],
        behavioral=["spiral swimming"],
    ),
}


class MockQwenClient:
    """Stand-in for Member 3. Returns canned findings by filename.

    Usage in the agent:
        agent = Agent(db_path=DB_PATH, qwen_client=MockQwenClient())
    """

    def __init__(self, canned: dict[str, ImageObservation] | None = None) -> None:
        self._canned = canned if canned is not None else DEFAULT_CANNED

    def analyze_image(self, image_path: str) -> ImageObservation:
        name = os.path.basename(image_path)
        if name in self._canned:
            return self._canned[name]
        return ImageObservation(
            quality_ok=False, note=f"no canned observation for {name}"
        )


# Findings whose text reads as behaviour rather than a static lesion map to
# `behavioral` so the retriever query and differential keywords still hit them.
_BEHAVIORAL_HINTS = (
    "gasping", "letharg", "swimming", "circling", "spiraling", "spinning",
    "isolation", "appetite", "breathing", "darting", "cluster", "crowding",
)


def _is_behavioral(text: str) -> bool:
    lowered = text.lower()
    return any(hint in lowered for hint in _BEHAVIORAL_HINTS)


def _vision_result_to_observation(result) -> ImageObservation:
    """Bridge Member 3's VisionResult -> Member 4's ImageObservation.

    Member 3 returns flat findings tagged with a `modality` (default "image").
    We split them into visual vs behavioural so the retriever query and the
    differential symptom-keyword matcher both get the right signal. Anything
    Qwen rejected (quality != USABLE) becomes a quality-not-ok observation
    with the reason attached, never a fabricated diagnosis.
    """
    quality = getattr(result, "quality", None)
    quality_ok = quality is not None and str(quality).lower() == "usable"
    note = getattr(result, "quality_reason", "") or (str(quality) if quality else "")

    visual: list[str] = []
    behavioral: list[str] = []
    for finding in getattr(result, "findings", []) or []:
        text = getattr(finding, "finding", "") or ""
        if not text:
            continue
        if _is_behavioral(text):
            behavioral.append(text)
        else:
            visual.append(text)

    return ImageObservation(
        visual=visual,
        behavioral=behavioral,
        quality_ok=quality_ok,
        note=note,
    )


class RealQwenAdapter:
    """Adapter that lets Member 4's agent call Member 3's real Qwen client.

    Member 3 ships `app.services.qwen_client.QwenClient` + `vision_analysis.
    analyze_image` which return a `VisionResult`; Member 4's agent speaks
    `ImageObservation`. This adapter closes that gap without Member 4 having
    to depend on Member 3's modules at import time.

    Construction is lazy: importing this class never touches Member 3's code.
    The real client is only built on the first `analyze_image` call, so the
    agent still starts cleanly when Member 3's branch has not landed on dev
    or when QWEN_API_KEY is unset (it then falls back to MockQwenClient).
    """

    def __init__(self, api_key: str | None = None, base_url: str | None = None,
                 model: str | None = None, fallback: "MockQwenClient | None" = None) -> None:
        self._api_key = api_key
        self._base_url = base_url
        self._model = model
        self._fallback = fallback if fallback is not None else MockQwenClient()
        self._client = None  # built lazily

    def _build_real_client(self):
        import os
        from app.services.qwen_client import QwenClient  # Member 3's module
        return QwenClient(
            api_key=self._api_key or os.environ.get("QWEN_API_KEY", ""),
            base_url=self._base_url or os.environ.get("QWEN_BASE_URL", ""),
            model=self._model or os.environ.get("QWEN_MODEL", ""),
        )

    def analyze_image(self, image_path: str) -> ImageObservation:
        # Lazy import: if Member 3's modules aren't on the path yet (their
        # branch hasn't merged to dev), fall straight back to the mock.
        try:
            from app.services.vision_analysis import analyze_image as m3_analyze
        except Exception:
            return self._fallback.analyze_image(image_path)

        try:
            if self._client is None:
                self._client = self._build_real_client()
            result = self._client.analyze_image(image_path)
        except Exception:
            # Any Qwen failure (no key, network, parse) must never block the
            # agent pipeline -- degrade to canned/mock observations.
            return self._fallback.analyze_image(image_path)

        return _vision_result_to_observation(result)

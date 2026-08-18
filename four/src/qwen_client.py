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

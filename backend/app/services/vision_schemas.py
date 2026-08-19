"""Structured output schemas for Qwen vision analysis (Member 3).

The vision layer returns observations only -- never a diagnosis.
"""

from enum import Enum

from pydantic import BaseModel, Field


class ImageQuality(str, Enum):
    """Usability assessment of an uploaded fish image."""

    USABLE = "usable"
    POOR_QUALITY = "poor_quality"
    NO_RELEVANT_SUBJECT = "no_relevant_subject"


class VisionFinding(BaseModel):
    """A single visible observation extracted from an image (not a diagnosis)."""

    finding: str
    region: str | None = None
    modality: str = "image"


class VisionResult(BaseModel):
    """Full structured result of one image analysis run."""

    quality: ImageQuality = ImageQuality.USABLE
    quality_reason: str = ""
    findings: list[VisionFinding] = Field(default_factory=list)
    metrics: dict | None = None

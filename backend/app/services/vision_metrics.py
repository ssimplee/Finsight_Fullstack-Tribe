"""Cost / observability metrics for vision calls (Member 3)."""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel


class VisionMetrics(BaseModel):
    """One record of a vision call, used for cost tracking and audit trails."""

    model: str
    latency_ms: int
    total_tokens: int | None = None
    retry_count: int = 0
    input_hash: str | None = None
    quality: str
    timestamp: str


def utc_now_iso() -> str:
    """UTC timestamp in ISO-8601 for a metrics record."""
    return datetime.now(timezone.utc).isoformat()
"""Uncertainty estimation.

Returns `low` / `medium` / `high` based on how much critical information is
missing and how close the top-ranked candidates are.
"""
from __future__ import annotations

from .models import CaseRecord, DifferentialItem


def assess(
    case: CaseRecord,
    missing: list[dict],
    diff: list[DifferentialItem],
    scores: dict[str, float],
) -> str:
    critical_missing = sum(1 for m in missing if m["importance"] == "critical")

    # Closeness of the top two scores indicates ambiguity.
    close_top2 = False
    if len(diff) >= 2:
        top_scores = sorted(scores.values(), reverse=True)
        close_top2 = (top_scores[0] - top_scores[1]) < 1.5

    no_evidence = len(diff) == 0

    if critical_missing >= 2 or no_evidence or (len(diff) >= 2 and close_top2):
        return "high"
    if critical_missing == 1 or len(diff) == 1:
        return "medium"
    return "low"

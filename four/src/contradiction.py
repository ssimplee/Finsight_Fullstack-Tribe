"""Contradiction detection across evidence modalities.

Detects when different modalities (visual, behavioural, water quality) point at
different candidate conditions — the overlapping-symptom scenario the project
is built around (worksplit §13 Priority 3).

Example output:
    image/visual findings point to Aeromonas (D02).
    water quality findings point to Water-quality stress / hypoxia (D05).
    Current findings have more than one explanation; additional evidence is
    needed to separate them.
"""
from __future__ import annotations

from .differential import CONDITION_NAMES, SYMPTOM_KEYWORDS
from .models import CaseRecord


def _match_conditions(text: str) -> set[str]:
    lowered = text.lower()
    return {
        cid
        for cid, keywords in SYMPTOM_KEYWORDS.items()
        if any(kw in lowered for kw in keywords)
    }


def _modality_conditions(case: CaseRecord) -> dict[str, set[str]]:
    """Map each modality to the conditions its signs most strongly match."""
    result: dict[str, set[str]] = {}

    visual_text = " ".join(case.observations.visual)
    if visual_text:
        result["image/visual"] = _match_conditions(visual_text)

    behavioral_text = " ".join(case.observations.behavioral)
    if behavioral_text:
        result["behaviour"] = _match_conditions(behavioral_text)

    wq = case.water_quality
    water_signals: list[str] = []
    if wq.dissolved_oxygen_mg_l is not None and wq.dissolved_oxygen_mg_l < 4:
        water_signals.append("low dissolved oxygen")
    if wq.ammonia_mg_l is not None and wq.ammonia_mg_l > 0.05:
        water_signals.append("high ammonia")
    if wq.nitrite_mg_l is not None and wq.nitrite_mg_l > 0.5:
        water_signals.append("high nitrite")
    if water_signals:
        # Any water-quality stress signal implicates environmental stress (D05).
        result["water quality"] = {"D05"}

    return result


def detect(case: CaseRecord) -> list[str]:
    """Return human-readable contradiction notes, or [] if none found."""
    modality_conds = _modality_conditions(case)
    notes: list[str] = []

    for modality, conds in modality_conds.items():
        for cid in sorted(conds):
            name = CONDITION_NAMES.get(cid, cid)
            notes.append(f"{modality} findings point to {name} ({cid}).")

    distinct = {cid for conds in modality_conds.values() for cid in conds}
    if len(distinct) >= 2:
        notes.append(
            "Current findings have more than one explanation; additional "
            "evidence is needed to separate them."
        )
    return notes

"""Missing-information detection.

Given a case, identify which important inputs are absent so the agent can
ask targeted follow-up questions instead of guessing.
"""
from __future__ import annotations

from .models import CaseRecord

# Water-quality fields that matter for triage, with importance ranking.
WATER_FIELDS = [
    ("dissolved_oxygen_mg_l", "dissolved oxygen", "critical"),
    ("temperature_c", "water temperature", "critical"),
    ("ammonia_mg_l", "ammonia", "critical"),
    ("nitrite_mg_l", "nitrite", "important"),
    ("ph", "pH", "important"),
    ("nitrate_mg_l", "nitrate", "secondary"),
]

# History fields that change the differential.
HISTORY_FIELDS = [
    ("mortality_trend", "mortality trend", "critical"),
    ("symptom_duration", "symptom duration", "important"),
    ("recent_introduction", "recent fish introduction", "important"),
    ("stocking_density_change", "stocking density change", "secondary"),
    ("transport_handling", "transport / handling", "secondary"),
    ("feed_change", "feed change", "secondary"),
    ("treatment", "recent treatment", "important"),
    ("water_change", "recent water change", "important"),
    ("filtration_failure", "filtration / oxygenation failure", "critical"),
    ("temperature_change", "recent temperature change", "secondary"),
]


def _why(field: str) -> str:
    reasons = {
        "dissolved_oxygen_mg_l": "Low dissolved oxygen can explain respiratory distress and surface gasping, which overlap with several infections.",
        "temperature_c": "High temperature predisposes to streptococcosis, columnaris, and TiLV, so it changes the differential.",
        "ammonia_mg_l": "Elevated ammonia damages gills and can mimic or complicate infectious disease.",
        "nitrite_mg_l": "Nitrite toxicity causes gasping and brownish gills, which can be confused with respiratory infection.",
        "ph": "Extreme pH adds stress and can mimic disease symptoms.",
        "nitrate_mg_l": "High nitrate indicates accumulated organic load and chronic water-quality stress.",
        "mortality_trend": "Mortality rate and pattern help separate fast-spreading infections from slower water-quality stress.",
        "symptom_duration": "Duration helps distinguish acute events from chronic disease.",
        "recent_introduction": "Recent introductions are a key risk factor for TiLV and other transmissible infections.",
        "stocking_density_change": "Density changes increase stress and transmission risk.",
        "transport_handling": "Handling stress can trigger streptococcosis and columnaris.",
        "feed_change": "Feed changes affect water quality and fish condition.",
        "treatment": "Knowing prior treatments prevents ineffective or harmful repetition.",
        "water_change": "Water changes and filtration failures directly affect ammonia, nitrite, and oxygen.",
        "filtration_failure": "A filtration or oxygenation failure can cause acute hypoxia and ammonia spikes.",
        "temperature_change": "Rapid temperature shifts stress fish and can trigger several diseases.",
    }
    return reasons.get(field, "This information helps narrow the differential diagnosis.")


def detect_missing(case: CaseRecord) -> list[dict]:
    """Return a list of missing items, ordered by importance."""
    missing: list[dict] = []

    wq = case.water_quality
    for field, label, importance in WATER_FIELDS:
        if getattr(wq, field) is None:
            missing.append(
                {"field": field, "label": label, "importance": importance, "why": _why(field)}
            )

    history = case.history or {}
    for field, label, importance in HISTORY_FIELDS:
        if field not in history or history.get(field) in (None, "", []):
            missing.append(
                {"field": field, "label": label, "importance": importance, "why": _why(field)}
            )

    if not case.images:
        missing.append(
            {
                "field": "images",
                "label": "fish image",
                "importance": "important",
                "why": "A photo lets the system extract visible findings for a better differential.",
            }
        )
    elif not case.observations.visual and not any(i.visible_findings for i in case.images):
        missing.append(
            {
                "field": "visual_observations",
                "label": "visual observations",
                "importance": "secondary",
                "why": "Explicit visual findings help ground the retrieved evidence.",
            }
        )

    if not case.observations.behavioral:
        missing.append(
            {
                "field": "behavioral_observations",
                "label": "behavioral observations",
                "importance": "secondary",
                "why": "Behavior such as swimming pattern or appetite strongly informs the differential.",
            }
        )

    order = {"critical": 0, "important": 1, "secondary": 2}
    missing.sort(key=lambda m: order.get(m["importance"], 3))
    return missing

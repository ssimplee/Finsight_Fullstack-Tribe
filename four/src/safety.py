"""Safety checks and safe-action generation.

Two jobs:
1. Detect unsupported diagnostic or treatment claims in generated text.
2. Produce safe recommended actions and escalation guidance.
"""
from __future__ import annotations

from .models import CaseRecord, DifferentialItem

# Phrases that would overstate certainty or prescribe treatment unsafely.
BLOCKED_PHRASES = [
    "definitely diagnosed",
    "definitive diagnosis",
    "confirmed diagnosis",
    "guaranteed cure",
    "this fish has",
    "immediately treat with",
    "administer antibiotics",
    "dose with",
]


def check_safety(text: str) -> list[str]:
    """Return any blocked phrases found in generated text."""
    lowered = text.lower()
    return [phrase for phrase in BLOCKED_PHRASES if phrase in lowered]


def build_recommended_actions(case: CaseRecord, diff: list[DifferentialItem]) -> list[str]:
    """Safe next steps. Always includes a confirmation step and a monitoring step."""
    actions: list[str] = [
        "Submit affected fish and a water sample for laboratory confirmation (culture, PCR, or histology as appropriate) before starting any treatment.",
        "Monitor the remaining stock closely and record mortality, behavior, and water quality twice daily.",
    ]

    top = diff[0].condition_id if diff else None
    if top == "D05":
        actions.append(
            "Increase aeration, perform a partial water exchange, pause feeding, and reduce stocking density."
        )
    elif top in ("D01", "D02", "D03", "D04"):
        actions.append(
            "Isolate affected fish where possible and avoid moving healthy stock between systems."
        )

    return actions


def build_escalation(diff: list[DifferentialItem]) -> list[str]:
    """Escalation triggers, populated when the top candidate warrants expert help."""
    escalation: list[str] = []
    if not diff:
        return escalation

    top = diff[0].condition_id
    # TiLV and high-uncertainty infectious candidates need professional input.
    if top == "D04":
        escalation.append(
            "Tilapia Lake Virus is a reportable, high-mortality disease. Contact a fish health professional or the competent authority immediately if suspected."
        )
    elif diff[0].uncertainty == "high":
        escalation.append(
            "The current evidence is too uncertain for confident management. Seek a fish health professional's assessment."
        )
    return escalation

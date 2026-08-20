"""Follow-up question generation.

Turns detected missing information into ranked, explainable questions. Every
question carries a `reason` so the report can explain why it was asked.
"""
from __future__ import annotations

from .models import AgentQuestion
from .missing_info import detect_missing

# field -> (question, reason override). Reasons default to the missing item's why.
QUESTION_TEMPLATES: dict[str, tuple[str, str]] = {
    "dissolved_oxygen_mg_l": (
        "What is the dissolved oxygen level (mg/L)?",
        "Low dissolved oxygen can explain respiratory distress and surface gasping, which overlap with several infections.",
    ),
    "temperature_c": (
        "What is the current water temperature?",
        "High temperature predisposes to streptococcosis, columnaris, and TiLV, so it changes the differential.",
    ),
    "ammonia_mg_l": (
        "What is the ammonia level (mg/L)?",
        "Elevated ammonia damages gills and can mimic or complicate infectious disease.",
    ),
    "nitrite_mg_l": (
        "What is the nitrite level (mg/L)?",
        "Nitrite toxicity causes gasping and brownish gills, which can be confused with respiratory infection.",
    ),
    "ph": (
        "What is the water pH?",
        "Extreme pH adds stress and can mimic disease symptoms.",
    ),
    "nitrate_mg_l": (
        "What is the nitrate level (mg/L)?",
        "High nitrate indicates accumulated organic load and chronic water-quality stress.",
    ),
    "mortality_trend": (
        "Has mortality changed recently, and how fast are fish dying?",
        "Mortality rate and pattern help separate fast-spreading infections from slower water-quality stress.",
    ),
    "symptom_duration": (
        "How long have the symptoms been present?",
        "Duration helps distinguish acute events from chronic disease.",
    ),
    "recent_introduction": (
        "Have new fish or fingerlings been introduced recently?",
        "Recent introductions are a key risk factor for TiLV and other transmissible infections.",
    ),
    "stocking_density_change": (
        "Has stocking density changed recently?",
        "Density changes increase stress and transmission risk.",
    ),
    "transport_handling": (
        "Have the fish been transported or handled recently?",
        "Handling stress can trigger streptococcosis and columnaris.",
    ),
    "feed_change": (
        "Has the feed or feeding rate changed recently?",
        "Feed changes affect water quality and fish condition.",
    ),
    "treatment": (
        "Have any treatments or medications been applied recently?",
        "Knowing prior treatments prevents ineffective or harmful repetition.",
    ),
    "water_change": (
        "Has there been a recent water change or filtration failure?",
        "Water changes and filtration failures directly affect ammonia, nitrite, and oxygen.",
    ),
    "filtration_failure": (
        "Has there been a recent filtration or oxygenation failure?",
        "A filtration or oxygenation failure can cause acute hypoxia and ammonia spikes.",
    ),
    "temperature_change": (
        "Has the water temperature changed suddenly?",
        "Rapid temperature shifts stress fish and can trigger several diseases.",
    ),
    "images": (
        "Can you provide a photo of the affected fish?",
        "A photo lets the system extract visible findings for a better differential.",
    ),
    "visual_observations": (
        "Can you describe any visible signs on the fish?",
        "Explicit visual findings help ground the retrieved evidence.",
    ),
    "behavioral_observations": (
        "Can you describe the fish's behavior, such as swimming pattern or appetite?",
        "Behavior strongly informs the differential diagnosis.",
    ),
}

# Questions used to reach the minimum of two when few fields are missing.
GENERIC_FALLBACKS: list[tuple[str, str]] = [
    (
        "Have mortality or stocking conditions changed recently?",
        "Recent stressors help separate infectious causes from water-quality stress.",
    ),
    (
        "Are other fish in the same system showing similar signs?",
        "Spread within the population helps distinguish contagious disease from environmental stress.",
    ),
]


def build_questions(case, min_questions: int = 2, max_questions: int = 4) -> list[AgentQuestion]:
    """Generate follow-up questions from missing information."""
    missing = detect_missing(case)
    questions: list[AgentQuestion] = []

    for item in missing:
        if len(questions) >= max_questions:
            break
        template = QUESTION_TEMPLATES.get(item["field"])
        if template is None:
            continue
        question, reason = template
        questions.append(
            AgentQuestion(
                question_id=f"Q_{len(questions) + 1:03d}",
                question=question,
                reason=reason,
            )
        )

    # Fill up to the minimum with generic questions if needed.
    for question, reason in GENERIC_FALLBACKS:
        if len(questions) >= min_questions:
            break
        questions.append(
            AgentQuestion(
                question_id=f"Q_{len(questions) + 1:03d}",
                question=question,
                reason=reason,
            )
        )

    return questions

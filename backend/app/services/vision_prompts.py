"""Prompt templates for Qwen visual observation (Member 3).

Core rule: the model must only report what is visible on the animal.
It must never name a disease, guess a pathogen or cause, or suggest treatment.
"""

from app.services.vision_terms import FEWSHOT_EXAMPLES, TILAPIA_OBSERVABLE_TERMS

VISION_SYSTEM_PROMPT = (
    "You are a careful visual observer for a fish-health triage assistant. "
    "You describe ONLY what is visible on the animal in the image. "
    "You never diagnose, never name diseases or pathogens, never guess causes, "
    "and never suggest treatments or medications."
)

_JSON_FORMAT = """JSON format:
{
  "quality": "usable" | "poor_quality" | "no_relevant_subject",
  "quality_reason": "short reason in english",
  "findings": [
    {"finding": "short visible observation in english", "region": "body area, e.g. flank / fin / eye / gill / mouth / whole body"}
  ]
}

Rules:
- "finding" must describe only what is visible (e.g. "red ulcer on flank"), never a conclusion.
- Do NOT include disease names, pathogens, causes, diagnoses or treatments in any field.
- If quality is not "usable", return an empty "findings" list.
- Output the JSON object only."""

_QUALITY_CHECK_PROMPT = """Judge whether this image is usable for visually inspecting a fish.

Answer with a single JSON object only:
{
  "quality": "usable" | "poor_quality" | "no_relevant_subject",
  "quality_reason": "short reason in english"
}

"no_relevant_subject" means the image does not show a fish or any fish part.
"poor_quality" means a fish is visible but too blurry, dark, small or occluded to observe reliably."""


def build_vision_prompt_with_terms(
    terms: list[str] | None = None,
    examples: list[str] | None = None,
) -> str:
    """Full vision prompt with an explicit finding vocabulary and few-shot examples."""
    terms = terms if terms is not None else TILAPIA_OBSERVABLE_TERMS
    examples = examples if examples is not None else FEWSHOT_EXAMPLES
    term_list = ", ".join(terms)
    example_block = "\n".join(f"- {ex}" for ex in examples)
    return (
        "Inspect the image and answer with a single JSON object only, no extra text.\n\n"
        "Steps:\n"
        "1. Judge whether the image is usable for visual inspection of a fish.\n"
        "2. If usable, list every visible abnormality on the fish "
        "(skin, scales, fins, eyes, gills, mouth, body shape).\n\n"
        f"Reference vocabulary for visible findings (observations only, never diseases):\n{term_list}\n\n"
        f"Examples of correct output:\n{example_block}\n\n"
        + _JSON_FORMAT
    )


def build_vision_prompt() -> str:
    """Full prompt for one-shot image observation (quality + findings)."""
    return build_vision_prompt_with_terms()


def build_quality_prompt() -> str:
    """Lightweight prompt for the standalone quality check."""
    return _QUALITY_CHECK_PROMPT
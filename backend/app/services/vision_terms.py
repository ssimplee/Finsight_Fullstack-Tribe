"""Observable-finding vocabulary and few-shot examples for Qwen vision (Member 3).

The vocabulary is observation-only: skin/surface signs visible on a Nile
tilapia. It must never contain disease names, pathogens or diagnoses, and can
later be merged with Member 2's conditions.json data.
"""

TILAPIA_OBSERVABLE_TERMS: list[str] = [
    "skin ulcer",
    "hemorrhage (red spots)",
    "exophthalmia (eye protrusion)",
    "fin erosion",
    "frayed fins",
    "abdominal distension",
    "scale loss",
    "body darkening",
    "gill pallor",
    "spinal curvature",
    "white spots",
    "redness (erythema)",
    "swelling",
    "opercular congestion",
    "emaciation (sunken belly)",
    "eye opacity",
    "mouth or jaw lesion",
]

TILAPIA_TERMS_CN: dict[str, str] = {
    "skin ulcer": "体表溃疡",
    "hemorrhage (red spots)": "出血点",
    "exophthalmia (eye protrusion)": "眼球突出",
    "fin erosion": "鳍腐蚀",
    "frayed fins": "鳍条破损",
    "abdominal distension": "腹胀",
    "scale loss": "掉鳞",
    "body darkening": "体色发黑",
    "gill pallor": "鳃色苍白",
    "spinal curvature": "脊柱弯曲",
    "white spots": "白点",
    "redness (erythema)": "皮肤发红",
    "swelling": "肿胀",
    "opercular congestion": "鳃盖充血",
    "emaciation (sunken belly)": "消瘦",
    "eye opacity": "眼球混浊",
    "mouth or jaw lesion": "口颌部病变",
}

FEWSHOT_EXAMPLES: list[str] = [
    '{"quality": "usable", "quality_reason": "fish is clearly visible", "findings": [{"finding": "red ulcer on flank", "region": "flank"}, {"finding": "frayed caudal fin", "region": "caudal fin"}]}',
    '{"quality": "no_relevant_subject", "quality_reason": "image shows a hand, not a fish", "findings": []}',
]
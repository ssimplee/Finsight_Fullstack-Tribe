"""Differential ranking.

Scores each candidate condition from (a) how much retrieved evidence supports
or conflicts with it and (b) how well observed symptoms match known keywords.
Returns ranked `DifferentialItem` objects plus raw scores for uncertainty.
"""
from __future__ import annotations

import re

from .models import CaseRecord, DifferentialItem, EvidenceItem

CONDITION_NAMES = {
    "D01": "Streptococcosis",
    "D02": "Motile Aeromonas Septicemia",
    "D03": "Columnaris disease",
    "D04": "Tilapia Lake Virus disease",
    "D05": "Water-quality stress / hypoxia",
}

# Weight of each evidence type when supporting a candidate condition.
# Keys match the `label` values produced by retriever.EVIDENCE_TYPE_LABELS,
# so a retrieved chunk's weight is looked up by its label, not its raw type.
# Aligned with Member 2's real evidence_type vocabulary.
EVIDENCE_WEIGHT = {
    "supporting evidence": 2.0,
    "risk factor": 1.5,
    "confirmation": 1.0,
    "safe action": 0.5,
    "conflicting evidence": -1.5,
}

# Symptom keywords per condition, used to weight observed signs.
# Note: both British (haemorrhag) and American (hemorrhag) spellings are listed
# because the FAO/WOAH knowledge base and case text use British spelling while
# earlier keywords used American -- without both, haemorrhage signs never hit.
SYMPTOM_KEYWORDS: dict[str, list[str]] = {
    "D01": [
        "exophthalmia", "pop-eye", "pop eye", "corneal", "spiral", "corkscrew",
        "erratic swimming", "loss of equilibrium", "letharg", "meningo",
        "haemorrhag",  # British spelling (FAO/WOAH style)
    ],
    "D02": [
        "ulcer", "scale loss", "frayed fin", "hemorrhag", "haemorrhag",
        "ascites", "abdominal distension", "fin rot", "flank",
        # Aeromonas-typical external lesions that disambiguate from Strep:
        "tail erosion", "fin erosion", "opercular",
    ],
    "D03": [
        "grey-white", "gray-white", "saddleback", "saddle", "necrotic patch",
        "gill necrosis", "whitened mouth", "mucus", "columnaris",
        # Columnaris-typical gill/skin signs that disambiguate from Aeromonas:
        "pale gill", "damaged gill", "gill damage", "skin patch", "white patch",
        "grey patch", "grey skin", "frayed fins",
    ],
    "D04": [
        "exophthalmia", "pop-eye", "pop eye", "darkening", "pale gill",
        "anemia", "skin hemorrhage", "skin haemorrhage", "abdominal distension",
        "letharg", "scale protrusion",
    ],
    "D05": [
        "gasp", "surface", "rapid breathing", "dart", "jump", "cluster",
        "brownish gill", "hypoxia", "ammonia", "nitrite", "low dissolved oxygen",
        # Behavioural emergency signals that accompany acute water-quality crisis:
        "crowding", "aeration", "aerator", "dawn",
    ],
}


def _case_text(case: CaseRecord) -> str:
    parts: list[str] = []
    parts.extend(case.observations.visual)
    parts.extend(case.observations.behavioral)
    for image in case.images:
        parts.extend(image.visible_findings)
    return " ".join(parts).lower()


def _symptom_hits(case: CaseRecord) -> dict[str, float]:
    text = _case_text(case)
    hits: dict[str, float] = {}
    for condition_id, keywords in SYMPTOM_KEYWORDS.items():
        score = 0.0
        for kw in keywords:
            if kw in text:
                score += 2.0
        hits[condition_id] = score
    return hits


# Clinical urgency / severity weighting (worksplit: prioritise high-impact
# causes when several are plausible). Unlike symptom-keyword scoring, this
# bonus fires only on GROUNDED urgency signals in the case, so it does not
# distort ordinary single-cause cases.
#
# D05 water-quality crisis: acute environmental emergency -> high boost when
#   low DO / high ammonia-nitrite / aeration-filtration failure / sudden mass
#   distress is actually present.
# D04 TiLV: reportable, high-mortality -> medium boost when reportable-signal
#   clues (recent fish movement, mass mortality, ocular+skin abnormalities)
#   are actually present.
# D01/D02/D03: treatable bacterial diseases -> no urgency boost (baseline).
URGENCY_BONUS = {"D05": 1.5, "D04": 1.0}
_EMERGENCY_WATER = {"aeration_failure", "filtration_failure", "oxygenation_failure"}
_MOVEMENT_KEYS = {"recent_introduction", "fish_movement", "stock_movement", "new_fish"}


def _urgency_bonus(case: CaseRecord) -> dict[str, float]:
    """Per-condition clinical-urgency bonus, grounded in actual case signals."""
    bonus = {cid: 0.0 for cid in CONDITION_NAMES}
    wq = case.water_quality
    history = case.history or {}
    history_text = " ".join(str(v) for v in history.values()).lower()

    # D05 environmental emergency. Tiered: a SEVERE acute emergency
    # (DO<3, or low DO combined with aeration failure + sudden mass distress)
    # means fish are dying now -> big boost to outrank chronic lesions.
    # A single mild signal -> smaller boost.
    do_low = wq.dissolved_oxygen_mg_l is not None and wq.dissolved_oxygen_mg_l < 4
    do_critical = wq.dissolved_oxygen_mg_l is not None and wq.dissolved_oxygen_mg_l < 3
    nh3_high = wq.ammonia_mg_l is not None and wq.ammonia_mg_l > 0.5
    no2_high = wq.nitrite_mg_l is not None and wq.nitrite_mg_l > 0.5
    aeration_fail = any(k in history for k in _EMERGENCY_WATER) or "aeration" in history_text or "aerator" in history_text
    sudden_mass = "sudden" in history_text and ("most" in history_text or "mass" in history_text)
    emergency_signals = sum([do_low, nh3_high, no2_high, aeration_fail, sudden_mass])
    if do_critical or (do_low and aeration_fail and sudden_mass) or emergency_signals >= 3:
        bonus["D05"] = URGENCY_BONUS["D05"] * 2.0  # severe acute: +3.0
    elif do_low or nh3_high or no2_high or aeration_fail or sudden_mass:
        bonus["D05"] = URGENCY_BONUS["D05"]  # single signal: +1.5

    # D04 TiLV reportable disease: recent fish movement/transfer, or mass /
    # unusual mortality. (Ocular+skin signs alone are NOT used -- Aeromonas
    # and Streptococcosis share exophthalmia + haemorrhage, so that combo is
    # not TiLV-specific and would falsely boost D04 on bacterial cases.)
    moved = any(k in history for k in _MOVEMENT_KEYS) or "movement" in history_text or "transfer" in history_text
    # Reported mortality trend (e.g. "Losses increased over the last 48 hours")
    # is a mass-mortality signal for TiLV. Scan the dedicated field so wording
    # like "losses increased" / "rising mortality" is caught, not just "mass".
    mortality = str(history.get("mortality_trend", "") or "").lower()
    mass_mortality = (
        "mass" in history_text
        or "unusual mortality" in history_text
        or any(kw in mortality for kw in ("loss", "increase", "ris", "died", "death"))
    )
    if moved or mass_mortality:
        bonus["D04"] = URGENCY_BONUS["D04"]

    return bonus


def score(case: CaseRecord, evidence: list[EvidenceItem]) -> dict[str, float]:
    """Compute a support score per candidate condition."""
    scores: dict[str, float] = {cid: 0.0 for cid in CONDITION_NAMES}

    # Symptom-keyword contribution from the case itself.
    for cid, hit_score in _symptom_hits(case).items():
        scores[cid] += hit_score

    # Evidence contribution.
    for item in evidence:
        cid = item.condition_id
        if cid not in scores:
            continue
        scores[cid] += EVIDENCE_WEIGHT.get(item.label, 0.0)

    # Clinical-urgency bonus (grounded in case signals, not arbitrary).
    for cid, b in _urgency_bonus(case).items():
        scores[cid] += b

    return scores


def _is_insufficient(case: CaseRecord) -> bool:
    """Decline to rank when the case carries almost no usable signal.

    Triggered when there are no real image findings AND no VISUAL observations
    (behavioural signs like lethargy alone are too non-specific to rank on) AND
    the critical water-quality triad (DO, temperature, ammonia) is mostly
    missing. Even if retrieval returns weakly-matching chunks, ranking on
    near-zero case signal would be guessing -> return an empty differential so
    the agent reports 'insufficient_evidence' and asks for more information
    instead (worksplit §13.7).
    """
    has_image_findings = any(
        f and f != "pending_qwen_observation" for img in case.images for f in img.visible_findings
    )
    has_visual = bool(case.observations.visual)
    wq = case.water_quality
    critical_missing = sum(
        1 for v in (wq.dissolved_oxygen_mg_l, wq.temperature_c, wq.ammonia_mg_l) if v is None
    )
    return (not has_image_findings) and (not has_visual) and critical_missing >= 2


def _classify(evidence: list[EvidenceItem], condition_id: str) -> tuple[list[str], list[str]]:
    supporting: list[str] = []
    conflicting: list[str] = []
    for item in evidence:
        if item.condition_id != condition_id:
            continue
        if item.label == "conflicting evidence":
            conflicting.append(item.evidence_id)
        else:
            supporting.append(item.evidence_id)
    return supporting, conflicting


def _strength(score: float) -> str:
    if score >= 6:
        return "strong"
    if score >= 3:
        return "moderate"
    return "weak"


def rank(
    case: CaseRecord, evidence: list[EvidenceItem], top_n: int = 3
) -> tuple[list[DifferentialItem], dict[str, float]]:
    """Return ranked differential items and the raw scores used for uncertainty."""
    # Insufficient case signal -> refuse to rank. Better to say "insufficient
    # evidence" and ask for more info than to guess from weak retrieval hits.
    if _is_insufficient(case):
        return [], score(case, evidence)

    scores = score(case, evidence)
    ranked_ids = sorted(scores, key=lambda cid: scores[cid], reverse=True)[:top_n]

    items: list[DifferentialItem] = []
    for rank_idx, cid in enumerate(ranked_ids, 1):
        if scores[cid] <= 0:
            continue
        supporting, conflicting = _classify(evidence, cid)
        items.append(
            DifferentialItem(
                condition_id=cid,
                rank=rank_idx,
                evidence_strength=_strength(scores[cid]),
                uncertainty="moderate",  # overwritten by uncertainty module
                supporting_evidence_ids=supporting,
                conflicting_evidence_ids=conflicting,
                confirmation_status="unconfirmed",
            )
        )

    return items, scores

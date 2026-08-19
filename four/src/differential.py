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
SYMPTOM_KEYWORDS: dict[str, list[str]] = {
    "D01": [
        "exophthalmia", "pop-eye", "pop eye", "corneal", "spiral", "corkscrew",
        "erratic swimming", "loss of equilibrium", "letharg", "meningo",
    ],
    "D02": [
        "ulcer", "scale loss", "frayed fin", "hemorrhag", "ascites",
        "abdominal distension", "fin rot", "flank",
    ],
    "D03": [
        "grey-white", "gray-white", "saddleback", "saddle", "necrotic patch",
        "gill necrosis", "whitened mouth", "mucus", "columnaris",
    ],
    "D04": [
        "exophthalmia", "pop-eye", "pop eye", "darkening", "pale gill",
        "anemia", "skin hemorrhage", "abdominal distension", "letharg",
    ],
    "D05": [
        "gasp", "surface", "rapid breathing", "dart", "jump", "cluster",
        "brownish gill", "hypoxia", "ammonia", "nitrite", "low dissolved oxygen",
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

    return scores


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

"""Evidence retrieval over the fish-disease knowledge base.

Builds a natural-language query from the case, queries ChromaDB, and returns
a list of `EvidenceItem` objects aligned with the shared contract.
"""
from __future__ import annotations

from typing import Optional

import chromadb

from .ingest import COLLECTION_NAME, build_collection
from .models import CaseRecord, EvidenceItem

# Evidence-type vocabulary used to label retrieved chunks.
# Aligned with Member 2's real knowledge_chunks.jsonl evidence_type values.
EVIDENCE_TYPE_LABELS = {
    "supporting": "supporting evidence",
    "risk_factor": "risk factor",
    "confirmation": "confirmation",
    "safe_action": "safe action",
    "conflicting": "conflicting evidence",
}


def _describe_water(wq) -> list[str]:
    """Turn non-null / abnormal water values into query phrases."""
    phrases: list[str] = []
    if wq.temperature_c is not None:
        t = wq.temperature_c
        if t >= 28:
            phrases.append(f"high water temperature {t} C")
        elif t <= 20:
            phrases.append(f"low water temperature {t} C")
        else:
            phrases.append(f"water temperature {t} C")
    if wq.ph is not None:
        if wq.ph < 6.5 or wq.ph > 8.5:
            phrases.append(f"abnormal pH {wq.ph}")
    if wq.dissolved_oxygen_mg_l is not None:
        if wq.dissolved_oxygen_mg_l < 4:
            phrases.append(f"low dissolved oxygen {wq.dissolved_oxygen_mg_l} mg/L")
    if wq.ammonia_mg_l is not None:
        if wq.ammonia_mg_l > 0.05:
            phrases.append(f"high ammonia {wq.ammonia_mg_l} mg/L")
    if wq.nitrite_mg_l is not None:
        if wq.nitrite_mg_l > 0.5:
            phrases.append(f"high nitrite {wq.nitrite_mg_l} mg/L")
    if wq.nitrate_mg_l is not None:
        if wq.nitrate_mg_l > 50:
            phrases.append(f"high nitrate {wq.nitrate_mg_l} mg/L")
    return phrases


def _describe_history(history: dict) -> list[str]:
    phrases: list[str] = []
    for key, value in history.items():
        if value not in (None, "", [], False):
            phrases.append(f"{key}: {value}")
    return phrases


def build_query(case: CaseRecord) -> str:
    """Build a single embedding query string from the multimodal case data."""
    parts: list[str] = []

    parts.extend(case.observations.visual)
    parts.extend(case.observations.behavioral)
    parts.extend(_describe_water(case.water_quality))
    parts.extend(_describe_history(case.history))

    for image in case.images:
        parts.extend(image.visible_findings)

    # Fallback so the query is never empty.
    if not parts:
        parts.append("Nile tilapia disease symptoms")

    return " ; ".join(parts)


class Retriever:
    def __init__(self, db_path: str = "fin_sight_db"):
        self._collection = build_collection(db_path)

    def retrieve(
        self,
        case: CaseRecord,
        n_results: int = 10,
        condition_id: Optional[str] = None,
        evidence_type: Optional[str] = None,
    ) -> list[EvidenceItem]:
        query = build_query(case)

        where: Optional[dict] = None
        if condition_id and evidence_type:
            where = {"$and": [
                {"condition_id": {"$eq": condition_id}},
                {"evidence_type": {"$eq": evidence_type}},
            ]}
        elif condition_id:
            where = {"condition_id": {"$eq": condition_id}}
        elif evidence_type:
            where = {"evidence_type": {"$eq": evidence_type}}

        results = self._collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where,
            include=["documents", "metadatas", "distances"],
        )

        evidence: list[EvidenceItem] = []
        docs = results.get("documents") or [[]]
        metas = results.get("metadatas") or [[]]
        for doc, meta in zip(docs[0], metas[0]):
            chunk_id = meta.get("chunk_id", "")
            evidence.append(
                EvidenceItem(
                    evidence_id=f"EVID_{chunk_id}",
                    condition_id=meta.get("condition_id"),
                    source_id=meta.get("source_id"),
                    label=EVIDENCE_TYPE_LABELS.get(
                        meta.get("evidence_type", ""), meta.get("evidence_type", "")
                    ),
                    text=doc,
                )
            )
        return evidence


# NOTE: no module-level singleton here. Instantiating `Retriever()` triggers the
# embedding model download, which should only happen lazily inside the Agent or
# the ingest script, not on a bare `import`.

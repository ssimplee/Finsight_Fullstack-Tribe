"""End-to-end demo runner using mock cases (no live Qwen needed).

    python run_demo.py
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.agent import Agent
from src.ingest import ingest
from src.models import (
    CaseImage,
    CaseRecord,
    FishInfo,
    Observations,
    WaterQuality,
)
from src.qwen_client import MockQwenClient

DB_PATH = "fin_sight_db"
MOCK_DATA = "mock_kb/knowledge_chunks.jsonl"


def case_clear_aeromonas() -> CaseRecord:
    """Flank ulcer + scale loss + high ammonia -> Aeromonas."""
    return CaseRecord(
        case_id="CASE_MOCK_CLEAR",
        fish=FishInfo(species="Nile tilapia"),
        observations=Observations(
            visual=["flank ulcer", "scale loss", "frayed fins"],
            behavioral=["lethargy", "reduced appetite"],
        ),
        water_quality=WaterQuality(
            temperature_c=29,
            dissolved_oxygen_mg_l=3.5,
            ammonia_mg_l=0.8,
            nitrite_mg_l=None,
            nitrate_mg_l=None,
            ph=None,
        ),
        history={"mortality_trend": "increasing", "recent_introduction": "no"},
    )


def case_incomplete() -> CaseRecord:
    """Only pop-eye, no water data -> should ask follow-ups, high uncertainty."""
    return CaseRecord(
        case_id="CASE_MOCK_INCOMPLETE",
        fish=FishInfo(species="Nile tilapia"),
        observations=Observations(visual=["exophthalmia"], behavioral=[]),
        water_quality=WaterQuality(),
        history={},
    )


def case_overlap() -> CaseRecord:
    """Pop-eye + hemorrhage + high temp -> Streptococcosis vs TiLV overlap."""
    return CaseRecord(
        case_id="CASE_MOCK_OVERLAP",
        fish=FishInfo(species="Nile tilapia"),
        observations=Observations(
            visual=["exophthalmia", "body hemorrhage", "darkening"],
            behavioral=["spiral swimming", "lethargy"],
        ),
        water_quality=WaterQuality(
            temperature_c=30,
            dissolved_oxygen_mg_l=4.5,
            ammonia_mg_l=0.1,
            nitrite_mg_l=None,
            nitrate_mg_l=None,
            ph=7.4,
        ),
        history={"mortality_trend": "rising fast", "recent_introduction": "yes"},
    )


def case_with_image() -> CaseRecord:
    """Image-only case; Qwen (mock) extracts visual findings from the photo."""
    return CaseRecord(
        case_id="CASE_MOCK_IMAGE",
        fish=FishInfo(species="Nile tilapia"),
        images=[CaseImage(image_id="IMG_001", filename="tilapia_dark_hemorrhage.jpg")],
        observations=Observations(visual=[], behavioral=[]),
        water_quality=WaterQuality(
            temperature_c=30,
            dissolved_oxygen_mg_l=4.0,
            ammonia_mg_l=0.2,
            nitrite_mg_l=None,
            nitrate_mg_l=None,
            ph=None,
        ),
        history={"mortality_trend": "rising fast", "recent_introduction": "yes"},
    )


def print_report(report) -> None:
    print("=" * 70)
    print(f"CASE: {report.case.case_id}")
    print(f"STATUS: {report.status}")
    print(f"SUMMARY: {report.summary}")
    print("\n-- follow-up questions --")
    for q in report.case.agent_questions:
        print(f"  [{q.question_id}] {q.question}")
        print(f"      why: {q.reason}")
    print("\n-- differential --")
    for d in report.case.differential:
        print(
            f"  #{d.rank} {d.condition_id} strength={d.evidence_strength} "
            f"uncertainty={d.uncertainty} support={len(d.supporting_evidence_ids)} "
            f"conflict={len(d.conflicting_evidence_ids)}"
        )
    print("\n-- recommended actions --")
    for a in report.case.recommended_actions:
        print(f"  - {a}")
    if report.case.escalation:
        print("\n-- escalation --")
        for e in report.case.escalation:
            print(f"  - {e}")
    obs = [e for e in report.case.retrieved_evidence if e.label == "OBSERVED"]
    if obs:
        print("\n-- observed evidence (OBS, from Qwen image) --")
        for e in obs:
            print(f"  [{e.evidence_id}] {e.text}")
    kb_count = len(report.case.retrieved_evidence) - len(obs)
    print(f"\n-- retrieved evidence: {kb_count} KB chunks --")
    print()


def main() -> None:
    # (Re)build the vector DB. upsert is idempotent, so this is safe to run
    # every time and keeps the DB in sync with the knowledge base.
    print("[ingest] (re)building vector DB from mock knowledge base...\n")
    ingest(MOCK_DATA, DB_PATH)

    # Pure-RAG agent: observations come from the case directly (no Qwen).
    rag_agent = Agent(db_path=DB_PATH)
    for builder in (case_clear_aeromonas, case_incomplete, case_overlap):
        report = rag_agent.run(builder())
        print_report(report)

    # Agent with Qwen image analysis (mock): image -> observations -> RAG.
    print("[qwen] running image case with MockQwenClient\n")
    qwen_agent = Agent(db_path=DB_PATH, qwen_client=MockQwenClient())
    report = qwen_agent.run(case_with_image())
    print_report(report)


if __name__ == "__main__":
    main()

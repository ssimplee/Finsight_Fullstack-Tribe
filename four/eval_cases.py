"""Run Member 2's real evaluation cases through the Member 4 RAG agent.

Loads each data/evaluation/cases/CASE_*.json, applies the follow-up script
answers, runs retrieve -> differential, and reports whether the top-ranked
condition matches the case's expected_top_condition_id.

Usage:
    cd four
    python eval_cases.py            # all cases
    python eval_cases.py CASE_003   # one case
"""
from __future__ import annotations

import json
import os
import sys

# Make `src` importable when run from four/.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.agent import Agent
from src.models import CaseRecord
from src.retriever import Retriever

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CASES_DIR = os.path.join(REPO_ROOT, "data", "evaluation", "cases")
DB_PATH = os.path.join(os.path.dirname(__file__), "fin_sight_db")


def _load_case(path: str) -> tuple[CaseRecord, dict]:
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    evaluation = raw.pop("evaluation", {})
    # CaseRecord mirrors backend/app/schemas/case.py fields.
    case = CaseRecord(**raw)
    return case, evaluation


def _apply_follow_up_script(case: CaseRecord, evaluation: dict) -> None:
    """Feed the case's canned follow-up answers back into agent_questions."""
    script = evaluation.get("follow_up_script", [])
    if not script:
        return
    # Build agent questions first so answer mapping has targets.
    if not case.agent_questions:
        from src import follow_up
        case.agent_questions = follow_up.build_questions(case)
    # Map script answers onto the generated questions by order; the script is a
    # gold answer set, so we attach each answer to the matching question id.
    for i, entry in enumerate(script):
        if i < len(case.agent_questions):
            case.agent_questions[i].answer = entry.get("answer", "")


def _expected_top(evaluation: dict) -> str | None:
    return evaluation.get("expected_top_condition_id")


def run_one(path: str, retriever: Retriever) -> dict:
    case, evaluation = _load_case(path)
    _apply_follow_up_script(case, evaluation)

    # Run the RAG stages directly (skip Qwen image step -- Member 2 pre-filled
    # visible_findings, exactly as the backend flow would after Member 3).
    case.retrieved_evidence = retriever.retrieve(case)
    from src import differential, uncertainty, missing_info, safety, contradiction
    diff, scores = differential.rank(case, case.retrieved_evidence)
    missing = missing_info.detect_missing(case)
    unc = uncertainty.assess(case, missing, diff, scores)
    for d in diff:
        d.uncertainty = unc
    case.differential = diff
    case.recommended_actions = safety.build_recommended_actions(case, diff)
    case.escalation = safety.build_escalation(diff)

    expected = _expected_top(evaluation)
    actual_top = diff[0].condition_id if diff else None
    # expected_top=None means the case should DECLINE to rank (insufficient
    # evidence). A None actual_top then counts as a hit.
    if expected is None:
        hit = actual_top is None
    else:
        hit = actual_top == expected

    return {
        "case_id": case.case_id,
        "case_type": evaluation.get("case_type", "?"),
        "expected_top": expected,
        "actual_top": actual_top,
        "actual_ranking": [d.condition_id for d in diff],
        "evidence_count": len(case.retrieved_evidence),
        "uncertainty": unc,
        "hit": hit,
    }


def main() -> None:
    if len(sys.argv) > 1:
        paths = [os.path.join(CASES_DIR, f"{c}.json") for c in sys.argv[1:]]
    else:
        paths = sorted(
            os.path.join(CASES_DIR, f)
            for f in os.listdir(CASES_DIR)
            if f.startswith("CASE_") and f.endswith(".json")
        )

    retriever = Retriever(db_path=DB_PATH)
    print(f"Running {len(paths)} cases through RAG...\n")
    hits = 0
    for path in paths:
        if not os.path.exists(path):
            print(f"  [skip] {path} not found")
            continue
        r = run_one(path, retriever)
        mark = "OK " if r["hit"] else ("-- " if r["hit"] is None else "XX ")
        print(f"{mark}{r['case_id']} [{r['case_type']}]")
        print(f"     expected top: {r['expected_top']}  actual top: {r['actual_top']}")
        print(f"     ranking: {r['actual_ranking']}  (evidence={r['evidence_count']}, unc={r['uncertainty']})")
        if r["hit"]:
            hits += 1
    judged = sum(1 for _ in paths if os.path.exists(_))
    print(f"\n{hits}/{judged} cases matched expected top condition.")


if __name__ == "__main__":
    main()

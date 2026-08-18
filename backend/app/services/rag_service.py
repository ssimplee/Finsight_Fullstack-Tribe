"""Member 4 real RAG + agent reasoning, wired into the backend.

Reuses the modules developed in four/src (retriever, missing_info,
differential, uncertainty, safety). The embedding model and Chroma DB live
under four/ so this service does not duplicate them.

Loading is lazy: importing this module does NOT touch chromadb or the model.
The backend still starts even if chromadb/sentence-transformers are absent;
case_service falls back to its mock in that case.
"""
from __future__ import annotations

import os
import sys

# Make four/src importable from the backend process.
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
_FOUR_DIR = os.path.join(_REPO_ROOT, "four")
if os.path.isdir(_FOUR_DIR) and _FOUR_DIR not in sys.path:
    sys.path.insert(0, _FOUR_DIR)

from app.schemas.case import CaseRecord, CaseReport


class RagService:
    """Real Member 4 RAG, replacing the mock branches in case_service."""

    def __init__(self, db_path: str | None = None) -> None:
        self._db_path = db_path or os.path.join(_FOUR_DIR, "fin_sight_db")
        self._retriever = None
        self._ready = False

    def _ensure_ready(self) -> None:
        """Lazy-load the retriever (triggers chromadb + model load)."""
        if self._ready:
            return
        from src.retriever import Retriever  # heavy: needs chromadb + model
        self._retriever = Retriever(db_path=self._db_path)
        self._ready = True

    def generate_follow_ups(self, case: CaseRecord):
        """Real follow-up questions from missing-information detection."""
        from src import follow_up as _follow_up
        return _follow_up.build_questions(case)

    def build_report(self, case: CaseRecord) -> CaseReport:
        """Run retrieve -> differential -> uncertainty -> safety.

        Uses the follow-up answers already collected on the case; does not
        regenerate follow-up questions (case_service handles that step).
        """
        self._ensure_ready()
        from src import differential as _differential
        from src import missing_info as _missing
        from src import safety as _safety
        from src import uncertainty as _uncertainty
        from src.differential import CONDITION_NAMES

        # 1. Retrieve evidence from the knowledge base.
        evidence = self._retriever.retrieve(case)
        case.retrieved_evidence = evidence

        # 2. Rank candidate conditions.
        diff, scores = _differential.rank(case, evidence)

        # 3. Assess uncertainty.
        missing = _missing.detect_missing(case)
        unc = _uncertainty.assess(case, missing, diff, scores)
        for d in diff:
            d.uncertainty = unc
        case.differential = diff

        # 4. Safe actions + escalation.
        case.recommended_actions = _safety.build_recommended_actions(case, diff)
        case.escalation = _safety.build_escalation(diff)

        if not diff:
            return CaseReport(
                case=case,
                status="insufficient_evidence",
                summary="Current evidence is insufficient for a meaningful ranking; "
                        "additional information and laboratory confirmation are required.",
            )

        top = diff[0]
        top_name = CONDITION_NAMES.get(top.condition_id, top.condition_id)
        others = ", ".join(
            CONDITION_NAMES.get(d.condition_id, d.condition_id) for d in diff[1:]
        )
        summary = (
            f"Top-ranked cause: {top_name} "
            f"(strength={top.evidence_strength}, uncertainty={unc})."
        )
        if others:
            summary += f" Alternatives considered: {others}."
        summary += " Findings are not confirmed; laboratory testing is required before treatment."
        return CaseReport(case=case, status="report_ready", summary=summary)


# Lazy singleton: construction is cheap, model loads on first build_report call.
rag_service = RagService()

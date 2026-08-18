"""Agent state machine: wires the reasoning modules into one flow.

    Intake -> ImageObs -> MissingInfo -> FollowUp
          -> Retrieve -> Differential -> Uncertainty -> Safety -> Report

Each step appends a trace entry (workflow log, not hidden model reasoning).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from . import differential, follow_up, missing_info, safety, uncertainty
from .differential import CONDITION_NAMES
from .models import CaseRecord, CaseReport, EvidenceItem
from .qwen_client import QwenClient
from .retriever import Retriever


@dataclass
class Agent:
    db_path: str = "fin_sight_db"
    qwen_client: QwenClient | None = None

    def __post_init__(self) -> None:
        self._retriever = Retriever(db_path=self.db_path)

    def run(self, case: CaseRecord) -> CaseReport:
        trace: list[str] = []
        missing: list[dict] = []

        # 1. Intake
        trace.append(f"Case {case.case_id} received "
                     f"(species={case.fish.species}, images={len(case.images)})")

        # 2. Image observation (Member 3's QwenClient). Falls back to pre-filled
        #    visible_findings when no client is injected, so the pipeline still
        #    runs in pure-RAG mode.
        obs_evidence: list[EvidenceItem] = []
        for image in case.images:
            findings: list[str] = list(image.visible_findings)
            behavioral: list[str] = []
            if not findings and self.qwen_client is not None:
                result = self.qwen_client.analyze_image(image.filename)
                if result.quality_ok:
                    findings = list(result.visual)
                    behavioral = list(result.behavioral)
                    image.visible_findings = list(findings)
                    image.source = "qwen_observation"
                else:
                    trace.append(
                        f"Image {image.image_id}: quality insufficient "
                        f"({result.note or 'unusable'})"
                    )
            case.observations.visual.extend(findings)
            case.observations.behavioral.extend(behavioral)
            for i, finding in enumerate(findings, 1):
                obs_evidence.append(
                    EvidenceItem(
                        evidence_id=f"OBS_{image.image_id}_{i:03d}",
                        condition_id=None,
                        source_id=image.image_id,
                        label="OBSERVED",
                        text=finding,
                    )
                )
        trace.append(
            f"Image observation: {len(case.observations.visual)} visual, "
            f"{len(case.observations.behavioral)} behavioral findings "
            f"({len(obs_evidence)} OBS evidence)"
        )

        # 3. Missing information
        missing = missing_info.detect_missing(case)
        trace.append(f"Missing information detected: {len(missing)} items")

        # 4. Follow-up questions
        case.agent_questions = follow_up.build_questions(case)
        trace.append(f"Follow-up questions asked: {len(case.agent_questions)}")

        # 5. RAG retrieval (OBSERVED evidence first, then retrieved KB evidence)
        retrieved = self._retriever.retrieve(case)
        case.retrieved_evidence = obs_evidence + retrieved
        trace.append(
            f"Evidence gathered: {len(obs_evidence)} observed + "
            f"{len(retrieved)} retrieved chunks"
        )

        # 6. Differential ranking
        diff, scores = differential.rank(case, case.retrieved_evidence)
        trace.append(f"Conditions compared: {len(diff)}")

        # 7. Uncertainty
        uncertainty_level = uncertainty.assess(case, missing, diff, scores)
        for item in diff:
            item.uncertainty = uncertainty_level
        trace.append(f"Uncertainty assessed: {uncertainty_level}")

        # 8. Safety + actions
        summary = self._build_summary(case, diff, uncertainty_level)
        violations = safety.check_safety(summary)
        case.recommended_actions = safety.build_recommended_actions(case, diff)
        case.escalation = safety.build_escalation(diff)
        case.differential = diff
        trace.append(f"Safety check passed" if not violations else f"Safety violations: {violations}")

        # 9. Report
        status = "needs_confirmation" if diff else "insufficient_evidence"
        report = CaseReport(case=case, status=status, summary=summary)

        return report

    @staticmethod
    def _build_summary(case: CaseRecord, diff, uncertainty_level: str) -> str:
        if not diff:
            return (
                "Current evidence is insufficient for a meaningful ranking. "
                "Additional information and laboratory confirmation are required."
            )

        top = diff[0]
        top_name = CONDITION_NAMES.get(top.condition_id, top.condition_id)
        others = ", ".join(
            CONDITION_NAMES.get(d.condition_id, d.condition_id) for d in diff[1:]
        )
        summary = (
            f"Top-ranked cause: {top_name} "
            f"(strength={top.evidence_strength}, uncertainty={uncertainty_level})."
        )
        if others:
            summary += f" Alternatives considered: {others}."
        summary += (
            " Findings are not confirmed; laboratory testing is required before treatment."
        )
        return summary

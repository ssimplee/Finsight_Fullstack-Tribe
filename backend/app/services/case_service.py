import logging
import os
import re
from uuid import uuid4

from fastapi import UploadFile
from starlette.concurrency import run_in_threadpool

from app.schemas.case import (
    AgentQuestion,
    CaseCreate,
    CaseImage,
    CaseRecord,
    CaseReport,
    CaseUpdate,
    DifferentialItem,
    EvidenceItem,
    FollowUpAnswers,
)
from app.services.qwen_client import QwenAPIError, QwenConfigError, QwenParseError
from app.services.vision_analysis import analyze_image
from app.services.vision_schemas import ImageQuality

logger = logging.getLogger(__name__)

# Member 4 real RAG is opt-in (env FINSIGHT_USE_RAG=1). Default uses the mock
# workflow so Member 1's tests and envs without chromadb keep working.
_USE_REAL_RAG = os.environ.get("FINSIGHT_USE_RAG", "").lower() in ("1", "true", "yes")

try:
    from app.services.rag_service import rag_service
except Exception:  # RAG deps (chromadb/sentence-transformers) not installed
    rag_service = None


_WATER_QUALITY_FIELDS = {
    "temperature_c",
    "ph",
    "dissolved_oxygen_mg_l",
    "ammonia_mg_l",
    "nitrite_mg_l",
    "nitrate_mg_l",
}

_YES_NO_HISTORY_FIELDS = {
    "recent_introduction",
    "stocking_density_change",
    "transport_handling",
    "feed_change",
    "treatment",
    "water_change",
    "filtration_failure",
    "temperature_change",
}


def _parse_numeric(answer: str) -> float | None:
    match = re.search(r"-?\d+(?:\.\d+)?", answer or "")
    if not match:
        return None
    try:
        return float(match.group())
    except ValueError:
        return None


def _apply_answer_to_case(case: CaseRecord, field_name: str | None, answer: str) -> None:
    """Feed a follow-up answer back into the structured fields the RAG
    differential and retriever actually read (water_quality / history)."""
    if not field_name or not answer:
        return
    answer = answer.strip()
    if not answer:
        return

    if field_name in _WATER_QUALITY_FIELDS:
        value = _parse_numeric(answer)
        if value is not None:
            setattr(case.water_quality, field_name, value)
        return

    history = case.history or {}
    case.history = history

    if field_name in _YES_NO_HISTORY_FIELDS:
        first = answer.lower().split(None, 1)[0].strip(".,;:")
        if first in {"yes", "true", "y", "yeah", "correct", "confirmed"}:
            history[field_name] = True
        # "no" / "unknown" answers carry no positive signal: do not add the key,
        # since differential._urgency_bonus keys on presence and would treat a
        # `False` value as a false positive.
        return

    history[field_name] = answer


class CaseService:
    def __init__(self) -> None:
        self._cases: dict[str, CaseRecord] = {}

    def create_case(self, payload: CaseCreate) -> CaseRecord:
        case_id = f"CASE_{uuid4().hex[:8].upper()}"
        case = CaseRecord(case_id=case_id, **payload.model_dump())
        self._cases[case_id] = case
        return case

    def get_case(self, case_id: str) -> CaseRecord | None:
        return self._cases.get(case_id)

    def update_case(self, case_id: str, payload: CaseUpdate) -> CaseRecord | None:
        case = self.get_case(case_id)
        if case is None:
            return None

        if payload.fish is not None:
            case.fish = payload.fish
        if payload.observations is not None:
            case.observations = payload.observations
        if payload.water_quality is not None:
            case.water_quality = payload.water_quality
        if payload.history is not None:
            case.history = payload.history

        return case

    async def attach_image(self, case_id: str, file: UploadFile) -> CaseRecord | None:
        case = self.get_case(case_id)
        if case is None:
            return None

        content = await file.read()
        visible_findings = await self._observe_image(content)

        image = CaseImage(
            image_id=f"IMG_{uuid4().hex[:8].upper()}",
            filename=file.filename or "upload",
            visible_findings=visible_findings,
        )
        case.images.append(image)
        return case

    async def _observe_image(self, content: bytes) -> list[str]:
        """Run Member 3 vision analysis; fall back to a pending marker on any failure."""
        if not content:
            return ["pending_qwen_observation"]
        try:
            result = await run_in_threadpool(analyze_image, content)
        except (QwenConfigError, QwenAPIError, QwenParseError):
            logger.warning("Qwen vision analysis unavailable; keeping pending marker.")
            return ["pending_qwen_observation"]
        except Exception:  # noqa: BLE001 - never block image upload on vision failure
            logger.warning("Qwen vision analysis failed unexpectedly; keeping pending marker.")
            return ["pending_qwen_observation"]
        if result.quality != ImageQuality.USABLE or not result.findings:
            return ["pending_qwen_observation"]
        return [finding.finding for finding in result.findings]

    def generate_follow_up_questions(self, case_id: str) -> list[AgentQuestion] | None:
        case = self.get_case(case_id)
        if case is None:
            return None

        if not case.agent_questions:
            # Member 4 real RAG follow-ups (falls back to mock if unavailable)
            if _USE_REAL_RAG and rag_service is not None:
                try:
                    case.agent_questions.extend(rag_service.generate_follow_ups(case))
                    return case.agent_questions
                except Exception:
                    pass  # fall through to mock

            questions = []
            if case.water_quality.dissolved_oxygen_mg_l is None:
                questions.append(
                    AgentQuestion(
                        question_id="Q_001",
                        question="What is the dissolved oxygen level?",
                        reason="Low dissolved oxygen can explain respiratory distress and surface gasping.",
                        field_name="dissolved_oxygen_mg_l",
                    )
                )
            if case.water_quality.ammonia_mg_l is None:
                questions.append(
                    AgentQuestion(
                        question_id="Q_002",
                        question="What is the ammonia level?",
                        reason="Ammonia stress can overlap with infectious disease signs and changes safe actions.",
                        field_name="ammonia_mg_l",
                    )
                )
            questions.append(
                AgentQuestion(
                    question_id=f"Q_{len(questions) + 1:03}",
                    question="Have mortality, stocking density, or recent handling conditions changed?",
                    reason="Recent stressors help separate infectious causes from water-quality stress.",
                )
            )
            for index, question in enumerate(questions, start=1):
                question.question_id = f"Q_{index:03}"
            case.agent_questions.extend(questions[:3])

        return case.agent_questions

    def answer_follow_up_questions(
        self, case_id: str, payload: FollowUpAnswers
    ) -> CaseRecord | None:
        case = self.get_case(case_id)
        if case is None:
            return None

        answers_by_id = {item.question_id: item.answer for item in payload.answers}
        for question in case.agent_questions:
            if question.question_id in answers_by_id:
                answer = answers_by_id[question.question_id]
                question.answer = answer
                _apply_answer_to_case(case, question.field_name, answer)

        return case

    def generate_report(self, case_id: str) -> CaseReport | None:
        case = self.get_case(case_id)
        if case is None:
            return None

        self.generate_follow_up_questions(case_id)
        answered_questions = [question for question in case.agent_questions if question.answer]

        if len(answered_questions) < 2:
            return CaseReport(
                case=case,
                status="needs_follow_up",
                summary="At least two follow-up answers are required before differential ranking.",
            )

        # Member 4 real RAG (falls back to mock if RAG deps unavailable)
        if _USE_REAL_RAG and rag_service is not None:
            try:
                return rag_service.build_report(case)
            except Exception as e:  # noqa: BLE001 - surface the failure instead of hiding it
                import traceback

                print(f"[case_service] RAG build_report FAILED: {e!r}", flush=True)
                traceback.print_exc()
                pass  # fall through to mock

        # --- mock fallback (original Member 1 logic) ---
        if not case.retrieved_evidence:
            case.retrieved_evidence.extend(
                [
                    EvidenceItem(
                        evidence_id="KB_MOCK_001",
                        condition_id="D05",
                        source_id="SRC_PENDING",
                        label="RETRIEVED EVIDENCE",
                        text="Low oxygen or poor water conditions can cause respiratory distress and surface gasping.",
                    ),
                    EvidenceItem(
                        evidence_id="KB_MOCK_002",
                        condition_id="D02",
                        source_id="SRC_PENDING",
                        label="RETRIEVED EVIDENCE",
                        text="Ulcers, scale loss, and lethargy may support bacterial disease when water stress does not fully explain the case.",
                    ),
                ]
            )

        if not case.differential:
            case.differential.extend(
                [
                    DifferentialItem(
                        condition_id="D05",
                        rank=1,
                        evidence_strength="moderate",
                        uncertainty="moderate",
                        supporting_evidence_ids=["KB_MOCK_001"],
                        conflicting_evidence_ids=[],
                    ),
                    DifferentialItem(
                        condition_id="D02",
                        rank=2,
                        evidence_strength="weak",
                        uncertainty="high",
                        supporting_evidence_ids=["KB_MOCK_002"],
                        conflicting_evidence_ids=["KB_MOCK_001"],
                    ),
                ]
            )
            case.recommended_actions.extend(
                [
                    "Confirm missing water-quality readings before treatment decisions.",
                    "Improve aeration and monitor affected fish while awaiting confirmed evidence.",
                ]
            )
            case.escalation.append(
                "Contact an aquatic animal health professional if mortality increases or severe lesions are present."
            )

        return CaseReport(
            case=case,
            status="mock_report_ready",
            summary="Mock report generated. Replace mock evidence with Member 2 data, Member 3 Qwen observations, and Member 4 RAG reasoning.",
        )


case_service = CaseService()

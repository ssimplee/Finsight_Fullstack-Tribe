from uuid import uuid4

from fastapi import UploadFile

from app.schemas.case import AgentQuestion, CaseCreate, CaseImage, CaseRecord, CaseReport


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

    async def attach_image(self, case_id: str, file: UploadFile) -> CaseRecord | None:
        case = self.get_case(case_id)
        if case is None:
            return None

        image = CaseImage(
            image_id=f"IMG_{uuid4().hex[:8].upper()}",
            filename=file.filename or "upload",
        )
        case.images.append(image)
        return case

    def generate_report(self, case_id: str) -> CaseReport | None:
        case = self.get_case(case_id)
        if case is None:
            return None

        if not case.agent_questions:
            case.agent_questions.extend(
                [
                    AgentQuestion(
                        question_id="Q_001",
                        question="What is the dissolved oxygen level?",
                        reason="Low dissolved oxygen can explain respiratory distress and surface gasping.",
                    ),
                    AgentQuestion(
                        question_id="Q_002",
                        question="Have mortality, stocking density, or recent handling conditions changed?",
                        reason="Recent stressors help separate infectious causes from water-quality stress.",
                    ),
                ]
            )

        return CaseReport(
            case=case,
            status="needs_follow_up",
            summary="Initial case created. Follow-up answers and RAG evidence are required before ranking causes.",
        )


case_service = CaseService()

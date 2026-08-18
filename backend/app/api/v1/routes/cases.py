from fastapi import APIRouter, HTTPException, UploadFile

from app.schemas.case import CaseCreate, CaseRecord, CaseReport
from app.services.case_service import case_service


router = APIRouter()


@router.post("", response_model=CaseRecord)
def create_case(payload: CaseCreate) -> CaseRecord:
    return case_service.create_case(payload)


@router.get("/{case_id}", response_model=CaseRecord)
def get_case(case_id: str) -> CaseRecord:
    case = case_service.get_case(case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


@router.post("/{case_id}/images", response_model=CaseRecord)
async def upload_case_image(case_id: str, file: UploadFile) -> CaseRecord:
    case = await case_service.attach_image(case_id, file)
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


@router.post("/{case_id}/report", response_model=CaseReport)
def generate_case_report(case_id: str) -> CaseReport:
    report = case_service.generate_report(case_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return report

# Backend

FastAPI service for case intake, image upload, AI/RAG orchestration, storage, and report output.

## Planned Responsibilities

- Validate shared case JSON.
- Store case/session state.
- Accept image uploads.
- Call Qwen image observation service.
- Call RAG/reasoning workflow.
- Return structured differential and report data to the frontend.

## Current Mock Endpoints

```text
GET    /api/v1/health
POST   /api/v1/cases
GET    /api/v1/cases/{case_id}
PATCH  /api/v1/cases/{case_id}
POST   /api/v1/cases/{case_id}/images
POST   /api/v1/cases/{case_id}/follow-up
POST   /api/v1/cases/{case_id}/follow-up/answers
POST   /api/v1/cases/{case_id}/report
```

These endpoints are enough for Postman/Apifox testing and frontend integration with mock data.

## Suggested Local Run

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Run tests from the repository root:

```powershell
pytest backend\tests
```

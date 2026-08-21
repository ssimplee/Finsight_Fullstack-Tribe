# Backend

FastAPI service for case intake, image upload, AI/RAG orchestration, storage, and report output.

## Planned Responsibilities

- Validate shared case JSON.
- Store case/session state.
- Accept image uploads.
- Call Qwen image observation service.
- Call RAG/reasoning workflow.
- Return structured differential and report data to the frontend.

## Current Endpoints

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

These endpoints are enough for Postman/Apifox testing and frontend integration.
Real RAG is optional for local stability; if it is not enabled or its
dependencies are missing, the report endpoint falls back to the Member 1 mock
report.

## Suggested Local Run

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

For real Member 4 RAG from the frontend, set this environment variable before
starting `uvicorn`:

```powershell
$env:FINSIGHT_USE_RAG="1"
uvicorn app.main:app --reload
```

Then make sure the RAG dependencies in `requirements.txt` are installed. If
`chromadb` or `sentence-transformers` are missing, the backend will still run
but `/cases/{case_id}/report` will return the mock fallback.

Run tests from the repository root:

```powershell
pytest backend\tests
```

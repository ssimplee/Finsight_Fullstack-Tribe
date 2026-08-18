# Backend

FastAPI service for case intake, image upload, AI/RAG orchestration, storage, and report output.

## Planned Responsibilities

- Validate shared case JSON.
- Store case/session state.
- Accept image uploads.
- Call Qwen image observation service.
- Call RAG/reasoning workflow.
- Return structured differential and report data to the frontend.

## Suggested Local Run

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

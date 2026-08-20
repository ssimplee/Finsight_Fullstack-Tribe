# Frontend

React/Next.js app for case intake, image upload, follow-up questions, and explainable report display.

## Planned Screens

- Case intake form.
- Image upload.
- Follow-up question view.
- Diagnostic report view.
- Evidence source viewer.

## Suggested Local Run

Start the backend first:

```powershell
cd backend
uvicorn app.main:app --reload
```

Then start the frontend:

```powershell
cd frontend
npm install
npm run dev
```

The frontend calls the backend through:

```text
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
```

This branch keeps frontend report data partly adapted for display, but case creation, image upload, follow-up question generation, follow-up answers, and report generation now go through the Member 1 FastAPI mock workflow.

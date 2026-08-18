# Architecture

```text
frontend
  -> backend FastAPI
    -> Qwen image observation
    -> missing-information detection
    -> RAG retrieval
    -> differential reasoning
    -> safe action/report response
```

## Directory Ownership

- `backend/`: Member 1, with integration hooks for Member 3 and Member 4.
- `frontend/`: Member 5.
- `shared/`: Member 1 owns contract stability; all members consume it.
- `data/`: Member 2.
- `docs/`: shared planning and API notes.
- `infra/`: deployment and environment setup.

## Team Mapping

- Member 1: Harry
- Member 2: JS
- Member 3: ShaoYou
- Member 4: Ziqing
- Member 5: beopgi

## First Milestone

Make one complete case work end to end with mock data, then replace each mock with the real data, Qwen, and RAG modules.

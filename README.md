# FOH Table Management

Front-of-House table management — Phase 1.

## Branches

- `feature/frontend-ui` — React UI with mock API
- `feature/backend` — FastAPI REST API + PostgreSQL/SQLite

## Structure

- `frontend/` — React UI (on `feature/frontend-ui`)
- `backend/` — FastAPI API (on `feature/backend`)

## Quick start (backend)

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

API: http://localhost:8000/docs

PostgreSQL: `docker compose up -d` then `DATABASE_URL=postgresql://foh:foh@localhost:5432/foh` in `backend/.env`.

## Connect frontend to backend

```env
VITE_USE_MOCK=false
VITE_API_URL=http://localhost:8000
```

Demo logins: `owner@foh.demo` / `demo1234` (see `backend/README.md`).

# ClientFlow

ClientFlow is a focused CRM-lite application for managing leads, quotations, and follow-ups. The v1 stack is React, TypeScript, Vite, Tailwind CSS, FastAPI, SQLAlchemy, and PostgreSQL.

## Prerequisites

- Python 3.11+
- Node.js 20.19+ (or 22.12+)
- Docker Desktop with Docker Compose

## 1. Start PostgreSQL

```powershell
docker compose up -d db
```

The development database is exposed on `localhost:5432`. Its non-production credentials match the default backend settings and can be overridden with `backend/.env`.

## 2. Start the API

```powershell
cd backend
Copy-Item .env.example .env
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
alembic upgrade head
python -m app.scripts.seed_demo_user
uvicorn app.main:app --reload --port 8000
```

Verify the API at <http://localhost:8000/api/v1/health> and view its interactive documentation at <http://localhost:8000/docs>.

## 3. Start the web app

In another terminal:

```powershell
cd frontend
Copy-Item .env.example .env
npm install
npm run dev
```

Open <http://localhost:5173>. The connection screen calls the FastAPI health endpoint and reports whether the API is available.

Development demo credentials:

```text
Email: demo@clientflow.app
Password: development-only-change-me
```

## Checks

```powershell
cd backend
pytest

cd ..\frontend
npm run lint
npm run build
npm run test:e2e
```

## Project plan

The approved product definition is in [`ClientFlow_v1_Full_Project_Design.md`](ClientFlow_v1_Full_Project_Design.md), and the implementation sequence is in [`session.md`](session.md).


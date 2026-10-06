# ClientFlow

ClientFlow is a production-deployed CRM-lite application for freelancers and small service teams. It turns a lead into a priced quotation, scheduled follow-up, and visible dashboard outcome without the overhead of a full sales platform.

[Open the live application](https://clientflow-web-abrarui12-kocw.onrender.com) · [Browse the API documentation](https://clientflow-api-abrarui12-kocw.onrender.com/docs) · [Read the case study](docs/case-study.md)

> The API runs on Render's free tier and can take about a minute to wake after inactivity.

## Try the public demo

| Field | Value |
| --- | --- |
| Email | `demo@clientflow.app` |
| Password | `ClientFlowDemo2026!` |
| Frontend | <https://clientflow-web-abrarui12-kocw.onrender.com> |
| API docs | <https://clientflow-api-abrarui12-kocw.onrender.com/docs> |

These credentials are intentionally public and are only for the portfolio deployment. Do not reuse the password elsewhere. The shared demo may contain records created by other visitors.

## Product at a glance

Small service businesses often track prospects in one tool, prepare prices in a spreadsheet, and remember follow-ups from chat history. That fragmentation makes ownership unclear, allows quote totals to drift, and hides the next action.

ClientFlow keeps the complete v1 workflow in one owned workspace:

```text
Login → qualify a lead → prepare an exact quotation → send/accept it
      → schedule or complete follow-ups → see the dashboard update
      → export a customer-ready PDF or a safe lead CSV
```

Core capabilities include:

- Authenticated, tenant-owned lead management with search, filters, pagination, editing, and archival.
- Server-authoritative quotations with decimal-safe line items, discounts, tax, legal state transitions, and PDF export.
- Timezone-aware follow-ups grouped as overdue, today, upcoming, or completed.
- One-request dashboard metrics for pipeline, open quotation value, reminders, and recent leads.
- Deterministic demo data, isolated demo reset, responsive layouts, keyboard workflows, and accessible feedback.
- PostgreSQL migrations, rollback-isolated tests, production configuration guards, and end-to-end browser coverage.

## Screenshots

All images use the deterministic fictional demo dataset at a consistent 1440×900 viewport.

| Dashboard | Lead detail |
| --- | --- |
| ![ClientFlow dashboard showing pipeline metrics, recent leads, and reminders](docs/screenshots/dashboard.png) | ![Lead detail showing contact information, quotations, and follow-ups](docs/screenshots/lead-detail.png) |

| Quotation builder | Generated PDF |
| --- | --- |
| ![Quotation builder showing line items and exact live totals](docs/screenshots/quotation-builder.png) | ![Generated customer quotation PDF](docs/screenshots/quotation-pdf.png) |

## Architecture

```mermaid
flowchart LR
    U[Browser] -->|HTTPS / JSON| W[React + TypeScript SPA<br/>Render Static Site]
    W -->|Bearer JWT · /api/v1| A[FastAPI service<br/>Render Web Service]
    A --> S[Validation + service layer<br/>SQLAlchemy transactions]
    S -->|PostgreSQL protocol| D[(Supabase PostgreSQL)]
    A -->|stream| E[PDF and CSV exports]
    G[GitHub Actions<br/>PostgreSQL 17] -->|lint · test · build| R[GitHub repository]
    R -->|Blueprint deploy| W
    R -->|Blueprint deploy| A
```

The browser owns interaction state; the API owns authentication, authorization, validation, transitions, and financial truth. Every business query is scoped to the authenticated user, and database work commits before a success response is sent.

See [Architecture and data design](docs/architecture.md) for the ER diagram, request flow, authorization model, quotation state machine, and money policy.

## Important engineering guarantees

### Ownership authorization

A bearer JWT identifies one active user. Leads are queried with that user's `owner_id`; quotations and follow-ups are authorized through their parent lead. A foreign UUID produces the same `404` as a missing record, which avoids leaking whether another tenant owns it. An OpenAPI inventory test ensures every business route has the authentication dependency.

### Exact money

The API rejects client-supplied totals. It uses Python `Decimal`, PostgreSQL `NUMERIC`, and `ROUND_HALF_UP` to calculate line totals, subtotal, discount, post-discount tax, and final total. The TypeScript builder provides a scaled-integer preview, but the saved API response is always authoritative.

### Legal quotation transitions

```text
DRAFT ──send──> SENT ──accept──> ACCEPTED
                    └──reject──> REJECTED
```

Only drafts can be edited. Accepted and rejected quotations are terminal. Sending can move an eligible lead to Quoted; accepting marks its lead Won in the same transaction. Row locks serialize concurrent transition attempts so only one conflicting action succeeds.

## Technology choices

| Layer | Technology | Reason |
| --- | --- | --- |
| Web | React 19, TypeScript 6, Vite 8 | Typed, fast SPA development with a small deployment surface |
| UI | Tailwind CSS 4, React Hook Form, Zod, Lucide | Responsive styling, accessible forms, shared client validation |
| Data fetching | TanStack Query 5 | Cache ownership, invalidation, retries, and loading/error states |
| API | FastAPI, Pydantic, SQLAlchemy 2 | Typed HTTP contracts, explicit validation, and composable owned queries |
| Database | PostgreSQL 17, Alembic, psycopg | Exact numeric types, constraints, row locks, sequences, and repeatable migrations |
| Security | Argon2id, PyJWT | Modern password hashing and short-lived signed access tokens |
| Documents | ReportLab, standards-based CSV | Server-owned exports using authoritative data |
| Testing | Pytest, Playwright, Ruff, oxlint, TypeScript | Database, API, browser, accessibility, and static quality gates |
| Hosting | Render + Supabase | Static CDN, Python service, managed PostgreSQL, and Blueprint IaC |

## Run locally

### Prerequisites

- Python 3.11 or newer
- Node.js 20.19+ or 22.12+
- Docker Desktop with Docker Compose, or an existing PostgreSQL server

### 1. Start PostgreSQL

The included Compose service starts the development PostgreSQL server. The test fixture creates the separate `_test` database on that same server when the suite first runs:

```powershell
docker compose up -d db
```

If you already have PostgreSQL, create two databases instead and set `DATABASE_URL` and `TEST_DATABASE_URL` to them. The test database name must end in `_test` because the suite rebuilds its `public` schema.

```text
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:PORT/clientflow
TEST_DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:PORT/clientflow_test
```

### 2. Install, migrate, and seed the API

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

The health endpoint is <http://localhost:8000/api/v1/health>. To expose Swagger locally, set `EXPOSE_API_DOCS=true` in `backend/.env`, then open <http://localhost:8000/docs>.

### 3. Install and start the web app

In another terminal:

```powershell
cd frontend
Copy-Item .env.example .env
npm install
npm run dev
```

Open <http://localhost:5173> and sign in with:

```text
Email: demo@clientflow.app
Password: development-only-change-me
```

### Environment configuration

Start from the checked-in example files; never commit `.env` files.

| Backend variable | Purpose |
| --- | --- |
| `DATABASE_URL` | SQLAlchemy PostgreSQL connection URL |
| `SECRET_KEY` | JWT signing secret; production requires at least 32 private bytes |
| `CORS_ORIGINS` | Comma-separated allowed frontend origins |
| `EXPOSE_API_DOCS` | Enables `/docs` and `/openapi.json` |
| `DEMO_USER_*` | Seeded account, profile, timezone, and currency settings |
| `TEST_DATABASE_URL` | Optional test-only PostgreSQL URL; must end in `_test` |

| Frontend variable | Purpose |
| --- | --- |
| `VITE_API_URL` | API base URL including `/api/v1` |
| `VITE_DEMO_EMAIL` | Optional login-page demo hint |
| `VITE_DEMO_PASSWORD` | Optional login-page demo hint |

Production additionally refuses the documented development database URL, wildcard or empty CORS origins, and weak/public signing secrets.

## Migrations and demo data

Alembic is the only schema creation path. Normal setup only needs the upgrade command:

```powershell
cd backend
alembic upgrade head
```

To verify a migration round trip against a disposable database:

```powershell
alembic downgrade base
alembic upgrade head
```

The normal seed is idempotent. It creates or reuses the demo account and adds 30 fictional leads, 8 quotations with 21 line items, and 12 relative follow-ups only when the dataset marker is absent:

```powershell
python -m app.scripts.seed_demo_user
```

Development-only reset deletes and recreates business records belonging to the demo user while preserving every other tenant:

```powershell
python -m app.scripts.seed_demo_user --reset
```

Reset is unconditionally disabled in production.

## Verification

```powershell
cd backend
pytest
python -m ruff check .

cd ..\frontend
npm run lint
npm run build
npm run test:e2e
```

The backend suite runs only on PostgreSQL. It creates the `_test` database if necessary, applies Alembic to a clean schema, and rolls every test back. Browser tests expect the migrated, seeded API on port 8000 and Vite on port 5173; they create uniquely named development records.

For the deployed system:

```powershell
cd frontend
npm run test:smoke:production
```

The production suite exercises the complete workflow, binary exports, double-click safety, keyboard behavior, 200% text, and responsive layouts.

## Repository map

```text
backend/       FastAPI app, services, models, migrations, scripts, and tests
frontend/      React application and Playwright browser tests
deployment/    Render/Supabase provisioning and verification guide
docs/          Architecture, case study, demo script, and screenshots
render.yaml    Production infrastructure Blueprint
session.md     Session-by-session implementation and acceptance record
AGENTS.md      Current engineering handoff and operating facts
```

## Production deployment

Render hosts the static frontend and Python API; Supabase hosts PostgreSQL. `render.yaml` defines exact origins, health checks, security headers, SPA routing, generated secrets, and provider-managed environment values. API startup applies migrations and the idempotent normal seed before serving traffic.

See [deployment/README.md](deployment/README.md) for provisioning, secret handling, connection-pool requirements, and public smoke checks.

## Known v1 limitations

- One owner represents one workspace; there are no teams, invitations, or role levels.
- Authentication uses access tokens only; there is no password reset, refresh-token rotation, or social login.
- Quotes use the owner's single configured currency and do not model payments, invoices, or exchange rates.
- Delivery is manual: “mark sent” records a workflow transition but does not email the PDF.
- Leads are archived rather than restored or permanently deleted through the UI.
- The shared public demo is not an isolated sandbox, and free hosting can cold-start.

## Possible v2 directions

- Team workspaces with roles, assignments, audit history, and activity feeds.
- Email delivery, reusable quote templates, approval links, invoices, and payment status.
- Refresh sessions, password recovery, MFA, rate limiting, and self-service onboarding.
- Custom pipeline stages, tags, imports, saved views, analytics, and scheduled reminder delivery.
- Background jobs, object storage for branded assets, observability, backups, and paid always-on hosting.

## Portfolio handoff

- [Architecture and data design](docs/architecture.md)
- [Engineering case study](docs/case-study.md)
- [60–90 second demo script](docs/demo-script.md)
- [Production deployment guide](deployment/README.md)
- [Locked v1 product design](ClientFlow_v1_Full_Project_Design.md)
- [Implementation and acceptance record](session.md)


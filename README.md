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

## Quotation calculation policy

The API is authoritative for quotation totals and does not accept client-supplied subtotal,
discount, tax, total, or line-total values. It calculates each line total first, rounds every
persisted money result to two decimal places using decimal `ROUND_HALF_UP`, applies the discount
to the subtotal, and then applies tax to the discounted subtotal. Quantities support three decimal
places; unit prices and percentages support two.

## Follow-up time policy

Follow-up timestamps must include a timezone offset and are stored as absolute instants. The API
groups incomplete reminders using the authenticated user's configured local calendar: dates before
today are overdue, the full local day is today, and tomorrow onward is upcoming. Completed reminders
are separate. Completion is idempotent, so a safe retry preserves the original completion time.

## Dashboard aggregation policy

Dashboard metrics include only the authenticated user's non-archived leads and their related data.
“Open quotations” means Draft and Sent quotations; both the count and value exclude accepted,
rejected, and archived-lead records. Upcoming dashboard reminders include today and future local
dates, while overdue reminders are due before the start of the user's current local day.

## Export safety and ownership

Quotation PDFs are generated from server-owned records and server-calculated totals. They include
the authenticated user's business profile, client identity, ordered items, dates, status, notes,
and a repeating item header when the document spans pages. Foreign quotation IDs return the same
not-found response as missing records.

Lead CSV exports include all non-archived leads owned by the authenticated user in a stable column
order. Dates are rendered in the user's configured timezone, decimals retain two places, and a
UTF-8 byte-order mark improves spreadsheet compatibility. User-entered text beginning with `=`,
`+`, `-`, or `@` (including after leading whitespace) is prefixed with an apostrophe to prevent
spreadsheet formula execution; Python's CSV writer handles commas, quotes, Unicode, and newlines.

## Project plan

The approved product definition is in [`ClientFlow_v1_Full_Project_Design.md`](ClientFlow_v1_Full_Project_Design.md), and the implementation sequence is in [`session.md`](session.md).


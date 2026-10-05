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

## Demo dataset and reset

The normal seed command creates the demo account plus a deterministic, screenshot-ready dataset of
30 leads, 8 quotations with 21 items, and 12 timezone-relative follow-ups. Running it again is a
no-op, so it is safe during normal development setup:

```powershell
cd backend
python -m app.scripts.seed_demo_user
```

To discard and recreate only the configured demo user's business records, use the explicit reset
flag. The demo account and password remain unchanged, and other users and their data are preserved:

```powershell
python -m app.scripts.seed_demo_user --reset
```

Reset is disabled when `ENVIRONMENT=production`. The normal production seed also requires replacing
the documented development-only demo password.

## Checks

```powershell
cd backend
pytest
python -m ruff check .

cd ..\frontend
npm run lint
npm run build
npm run test:e2e
```

The backend suite runs entirely against PostgreSQL. By default it uses
`postgresql+psycopg://clientflow:clientflow@localhost:5432/clientflow_test` (the Docker Compose
server), creates that database if it is missing, and builds its schema from the Alembic
migrations on every run. Each test runs inside a transaction that is always rolled back. To use
another server, set `TEST_DATABASE_URL`. The database name must end in `_test`, because the suite
drops and rebuilds its schema.

`npm run test:e2e` expects the API on port 8000 and the web app on port 5173 to be running against
a migrated, seeded development database. The browser tests create uniquely named records there.

## Production deployment

Live portfolio deployment:

- Application: <https://clientflow-web-abrarui12-kocw.onrender.com>
- API documentation: <https://clientflow-api-abrarui12-kocw.onrender.com/docs>

Public demo credentials:

```text
Email: demo@clientflow.app
Password: ClientFlowDemo2026!
```

The free API can require a short cold start after inactivity.

The repository includes a Render Blueprint for the HTTPS static frontend and FastAPI service, a
Supabase PostgreSQL setup guide, an idempotent migrate-and-seed start command, and PostgreSQL-backed
GitHub Actions checks. No production credential is stored in Git. Follow
[`deployment/README.md`](deployment/README.md) to provision and verify the public deployment.

## Security and reliability safeguards

- Every API route except health and login requires a valid bearer token. Tokens must carry an
  expiry, issue time, subject, and type. Login failures are identical for unknown emails, wrong
  passwords, and inactive accounts.
- Every record query is scoped to the authenticated owner. Another account's IDs return the same
  `404` as missing records.
- Each request's database work is committed or rolled back before the response is sent.
  Quotation and follow-up changes lock their row, so concurrent conflicting actions resolve to one
  success and one `409`.
- With `ENVIRONMENT=production`, the API refuses to start without a private `SECRET_KEY` of at
  least 32 bytes, a real `DATABASE_URL`, and explicit `CORS_ORIGINS`. CORS allows only the
  configured origins, the GET/POST/PATCH methods, and the headers the web app sends.
- Validation errors never echo submitted values, and unexpected errors return no internal details.
- Archiving a lead also hides its quotations and follow-ups from lists, detail pages, and PDFs,
  matching the dashboard. The records remain stored.

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

## UX and accessibility

ClientFlow uses keyboard-accessible native dialogs for mobile navigation, archive confirmation,
follow-up editing, and irreversible quotation transitions. Focus returns to the invoking control,
validation errors are associated with form fields, icon-only controls have accessible names, and
success/error notifications are announced through live regions. Every route has a meaningful
document title and unknown paths show a useful 404 page.

The primary routes are regression-tested at mobile, tablet, laptop, and wide-desktop widths, plus
200% text enlargement. The UI honors reduced-motion preferences and uses text labels—not color
alone—for lead and quotation states.

## Project plan

The approved product definition is in [`ClientFlow_v1_Full_Project_Design.md`](ClientFlow_v1_Full_Project_Design.md), and the implementation sequence is in [`session.md`](session.md).


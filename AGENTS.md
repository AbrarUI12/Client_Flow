# ClientFlow Agent Handoff

Last updated: 2026-10-05, while Session 14 production preparation is locally verified and public
deployment is waiting for the user's hosting-account connection.

This file is the fast-start handoff for any new coding session. Read it before making changes,
then read the current session in `session.md`. Keep this file current whenever a session changes
state, architecture, commands, environment assumptions, known issues, or remaining work. Every
session commit must update both its status in `session.md` and the relevant sections here.

## Product and scope

ClientFlow is a portfolio-quality CRM-lite application for freelancers and small service teams. Its
complete v1 flow is: authenticate, manage owned leads, prepare decimal-safe quotations, schedule and
complete follow-ups, view operational dashboard data, export quotation PDFs and lead CSV, and use a
repeatable demo dataset.

The source of truth is:

- `ClientFlow_v1_Full_Project_Design.md` for the locked product and architecture definition.
- `session.md` for the detailed Session 0-15 execution plan and acceptance gates.
- This file for the concise current-state handoff.

Do not broaden v1 beyond those documents unless the user explicitly changes scope.

## Repository and delivery protocol

- Workspace: `D:\projects\Client_Flow`
- GitHub: `https://github.com/AbrarUI12/Client_Flow.git`
- Branch: `main`; remote: `origin`
- Delivery rule from the user: finish one session completely, verify it, commit it, push it, and only
  then start the next session.
- Preserve unrelated user changes. Use `apply_patch` for source edits.
- Before each session commit: run relevant backend tests, backend Ruff, frontend lint, frontend
  production build, browser tests, and `git diff --check`.
- Use the suggested commit message in `session.md` when practical.
- After a successful push, record the commit here and update the next-session pointer.

## Technology and structure

- Frontend: React 19, TypeScript 6, Vite 8, Tailwind CSS 4, React Router 7, TanStack Query 5,
  React Hook Form, Zod, Lucide, Playwright.
- Backend: Python 3.11+, FastAPI, Pydantic, SQLAlchemy 2, Alembic, PostgreSQL 17, psycopg,
  Argon2, PyJWT, ReportLab.
- Database entities already present: `User`, `Lead`, `Quotation`, `QuotationItem`, `FollowUp`.
- API prefix: `/api/v1`.
- Backend organization: routes under `backend/app/api/v1`, validation under `schemas`, business
  behavior under `services`, ownership enforced in database queries, and request-scoped commit or
  rollback in `dependencies/database.py`.
- Frontend organization: feature folders under `frontend/src/features`, central authenticated fetch
  wrapper in `lib/apiClient.ts`, query-key factories per feature, protected routes inside `AppShell`.

## Local setup and commands

Normal documented setup uses Docker PostgreSQL on port 5432:

```powershell
docker compose up -d db
cd backend
Copy-Item .env.example .env
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
alembic upgrade head
python -m app.scripts.seed_demo_user
uvicorn app.main:app --reload --port 8000

cd ..\frontend
Copy-Item .env.example .env
npm install
npm run dev
```

Core verification:

```powershell
cd backend
pytest
python -m ruff check .

cd ..\frontend
npm run lint
npm run build
npm run test:e2e
```

The whole backend suite runs on PostgreSQL. `TEST_DATABASE_URL` defaults to
`postgresql+psycopg://clientflow:clientflow@localhost:5432/clientflow_test`, which matches Docker
Compose. The fixture creates the database if needed, refuses any name that does not end in `_test`,
drops and rebuilds its `public` schema with Alembic once per run, and runs each test inside a
rolled-back outer transaction. On this workstation Docker is unavailable, so an ignored portable
PostgreSQL 17.11 installation exists under `.tmp/postgres-portable` on `127.0.0.1:55432`:

```text
Dev/demo database (API, Playwright): postgresql+psycopg://postgres@127.0.0.1:55432/clientflow
Backend tests:                       postgresql+psycopg://postgres@127.0.0.1:55432/clientflow_test
```

Start the cluster from the repository root:

```powershell
.tmp\postgres-portable\pgsql\bin\pg_ctl.exe -D .tmp\postgres-portable\data -l .tmp\postgres-portable\postgres.log -o "-p 55432 -h 127.0.0.1" -w start
```

It was terminated externally once during Session 13 and recovered cleanly. Run the API with
`DATABASE_URL` set to the dev database (no `backend/.env` exists here). Playwright needs Uvicorn on
8000 and Vite on 5173 already running and writes uniquely named records into the dev database. Do
not commit `.tmp`. Always verify process state rather than assuming it.

Demo credentials (development-only, intentionally public):

```text
Email: demo@clientflow.app
Password: development-only-change-me
Timezone: Asia/Dhaka
Currency: BDT
```

## Completed sessions and pushed commits

| Session | Result | Commit |
| --- | --- | --- |
| 0-1 | Locked specification/architecture and created the full-stack repository foundation | `1f69e3c` |
| 2 | Added all SQLAlchemy models, constraints, indexes, PostgreSQL sequence, initial Alembic migration, and idempotent demo-user seed | `e4a9583` |
| 3 | Added Argon2/JWT auth, `/auth/login`, `/auth/me`, semantic logout, tab-scoped token storage, protected responsive shell, and auth browser test | `ab1baa8` |
| 4 | Added owned lead create/list/detail/update/archive API with validation, search, filters, pagination, and cross-user tests | `1090448` |
| 5 | Added responsive lead list/cards, URL filters, debounced search, reusable create/edit form, detail and archive flow, with desktop/mobile tests | `1d04b8d` |
| 5 follow-up | Aligned frontend lead sources with backend values (LinkedIn, Upwork, Fiverr, etc.) | `2a6dad7` |
| 6 | Added server-authoritative quotation arithmetic, PostgreSQL sequence numbers, atomic item replacement, lists, ownership, and legal state transitions | `904bbba` |
| 7 | Added exact-decimal quotation builder, list, detail, lead summaries, draft edit/send/accept UI, and lead-to-won browser flow | `bd30fc3` |
| 8 | Added timezone-aware follow-up scheduling, owned grouping, editing, idempotent completion, lead dialog/summaries, responsive grouped UI, and browser coverage | `6d81880` |
| 9 | Added one-request owned dashboard metrics, pipeline counts, reminder/recent-lead read models, responsive UI, PostgreSQL aggregation tests, and browser refresh coverage | `4bfc7e7` |
| 10 | Added owned paginated quotation PDFs and safe active-lead CSV exports, authenticated browser downloads, content tests, and mobile coverage | `3f71881` |
| 11 | Added deterministic screenshot-ready demo data, idempotent normal seed, isolated demo-only reset, production refusal, and tenant-preservation tests | `439e9e6` |
| 12 | Added coherent responsive polish, shared notifications, focus-managed confirmations/navigation, accessible forms/titles/404, and multi-breakpoint browser coverage | `5f9af7c` |
| 13 | PostgreSQL-only rollback-isolated suite (128 tests), audit-driven security/reliability fixes, commit-before-response sessions, production config guards, row locks, archive consistency, and a double-click-safe MVP browser test | `e992556` |

Sessions 0-13 are marked implemented and verified in `session.md` and are on `origin/main`.

## Important implemented behavior

### Authentication

- Bearer JWT access tokens live in `sessionStorage`, not persistent local storage.
- The central API client attaches auth and emits an unauthorized event on 401.
- Login errors do not distinguish unknown users from bad passwords.
- Every business route depends on the current active user. A route-inventory test checks this
  against OpenAPI.
- JWT decoding requires `exp`, `iat`, `sub`, and `type`. Passwords are Argon2id.
- The frontend clears the TanStack Query cache at login, logout, and 401, so one account's cached
  data never renders for the next account in the same tab.

### Transactions, validation, and production configuration

- `DbSession` in `dependencies/database.py` is the only database dependency. It is function-scoped,
  so the commit or rollback finishes before the response is sent. Routes and `get_current_user`
  share one session per request.
- Quotation edit/status and follow-up edit/complete load their row with `SELECT ... FOR UPDATE`, so
  concurrent conflicting actions serialize and the loser gets the normal 409.
- Request schemas extend `schemas/common.py:RequestModel`, which rejects NUL characters with 422.
  Shared list query parameters in `api/v1/params.py` bound `page` to 100,000 and validate
  `search`. Out-of-range follow-up dates return 422.
- The 422 handler omits submitted `input` values, so passwords are never echoed and malformed
  Unicode cannot crash the response. Unhandled errors return a plain `Internal Server Error` without
  details.
- With `ENVIRONMENT=production`, `Settings` refuses a public or under-32-byte `SECRET_KEY`, the
  development `DATABASE_URL`, and wildcard or empty `CORS_ORIGINS`. CORS allows only
  GET/POST/PATCH with `Accept`, `Authorization`, and `Content-Type`, exposes
  `Content-Disposition`, and does not allow credentials.

### Leads

- All lead access is scoped by `owner_id`; foreign records return the same structured 404 as missing
  records.
- Archived leads disappear from normal detail and list queries. Their quotations and follow-ups
  are also hidden from every list, detail, mutation, and PDF route (structured 404), which keeps the
  feature pages consistent with dashboard metrics. The rows remain stored.
- Lists support escaped case-insensitive search, status/source filters, deterministic ordering, and
  pagination.
- Frontend pages: `/leads`, `/leads/new`, `/leads/:id`, `/leads/:id/edit`.

### Quotations

- The API rejects client-supplied totals. It calculates line totals, subtotal, discount, post-
  discount tax, and final total with `Decimal` and `ROUND_HALF_UP` to two money decimals.
- Quantities allow three decimal places; prices and percentages allow two.
- Production quote numbers use the concurrency-safe PostgreSQL `quotation_number_seq` and format
  `Q-YYYY-NNNNNN`.
- Legal transitions: `DRAFT -> SENT -> ACCEPTED|REJECTED`; accepted/rejected are terminal.
- Only drafts are editable. Sending marks an eligible lead quoted; accepting marks the lead won in
  the same transaction; rejecting does not mark the lead lost.
- Frontend pages: `/quotations`, `/quotations/:id`, `/quotations/:id/edit`, and
  `/leads/:leadId/quotes/new`.
- The builder preview uses scaled `BigInt` arithmetic and the API remains authoritative after save.

### Follow-ups

- API routes create under an owned active lead, list with optional lead/group filters, edit only
  incomplete records, and complete with ownership through the related lead.
- Due timestamps require an explicit offset. Incomplete reminders are grouped by the user's local
  calendar date: before today is overdue, the full local day is today, and tomorrow onward is
  upcoming. Completed records are separate and ordered by completion time.
- Completion is intentionally idempotent: retries return the completed record without replacing its
  original `completed_at`.
- Lead detail has a native accessible create/edit dialog and reminder summaries. `/follow-ups` has
  responsive overdue/today/upcoming/completed sections, lead links, editing, and immediate complete
  actions. Mutations invalidate follow-up, lead, and future dashboard queries.

### Dashboard

- `GET /api/v1/dashboard/summary` is the one primary dashboard request and applies current-user
  ownership plus non-archived lead filtering to every metric and row.
- Open quotations are explicitly Draft + Sent; count and value exclude terminal quotes and quotes
  under archived leads. Upcoming reminder rows include today and future dates; overdue uses the
  start of the user's current local day.
- The UI has four linked metric cards, a complete numeric pipeline, recent leads, overdue/upcoming
  reminders, layout-preserving skeletons, retry and empty states, and responsive laptop/mobile
  layouts. Lead, quotation, and follow-up mutations invalidate `['dashboard']` queries.

### Exports

- `GET /api/v1/quotations/{id}/pdf` uses the existing owned quotation query before ReportLab
  rendering. The document contains business/client identity, dates, status, ordered items,
  authoritative totals, optional notes, page numbering, and an automatically repeated item header
  for long documents.
- `GET /api/v1/leads/export` exports every current-user non-archived lead in deterministic order.
  Its stable columns use readable enums, exact two-decimal values, local-time dates, UTF-8 BOM,
  standards-based CSV quoting, and apostrophe neutralization for formula-leading user text.
- The central frontend API client supports authenticated binary downloads and filenames exposed by
  `Content-Disposition`. Lead list and quotation detail expose pending/error-aware download actions.
- `pypdf` is a backend development dependency used to extract PDF content and verify page counts;
  ReportLab remains the runtime PDF generator.

### Demo data and reset

- `python -m app.scripts.seed_demo_user` creates or reuses the demo account and adds a canonical
  dataset only when its deterministic marker is absent. A repeat run is a no-op.
- The dataset contains 30 fictional leads covering every lead status and all eight source values,
  eight quotations covering Draft/Sent/Accepted/Rejected with 21 calculated line items, and 12
  follow-ups split evenly across overdue/today/upcoming/completed relative to the seed date.
- Stable UUIDv5 identifiers and reserved high-range display quote numbers make screenshots and
  reset assertions predictable while dates stay useful whenever the data is reseeded.
- `python -m app.scripts.seed_demo_user --reset` deletes quotation items, follow-ups, quotations,
  and leads belonging only to the configured demo user, then recreates the dataset transactionally.
  It preserves the user/password and every other tenant. Reset is unconditionally refused when
  `ENVIRONMENT=production`.

### UX, responsive behavior, and accessibility

- The shell has a native modal mobile navigation drawer with initial focus, Escape/backdrop close,
  focus return, active text labels, and no fake notification control. Unknown authenticated paths
  render an actionable 404 instead of silently redirecting.
- Shared live-region toasts announce mutation/download success and errors. Native confirmation
  dialogs protect archive and terminal/locking quotation transitions and prevent repeated actions
  while pending.
- Login, lead, follow-up, and quotation validation errors are visibly and programmatically linked
  to their controls. Global focus-visible and reduced-motion rules cover all interactive elements.
- Page titles follow the current route. Status badges always include text. Tutorial/placeholder
  copy, the unused placeholder dashboard, and Vite/React starter assets were removed.
- Playwright checks keyboard activation, dialog focus/return, useful 404 behavior, notification
  feedback, mobile 200% text, and no page overflow at 390/768/1280/1600 widths. Manual screenshot
  QA covered the populated desktop dashboard and mobile lead list.

## Current session: Session 14

Session 13 and its handoff are pushed as `e992556` and `6a8d961`. Session 14 repository preparation
is pushed as `39bcc0b`; the Supabase provider switch is pushed as `13ad531`. Session 14 must not be
marked complete until the public deployment and smoke test pass.

Implemented and pushed for Session 14:

- Selected Render Singapore for the free Python API, Render's global static CDN for the frontend,
  and Supabase Singapore for PostgreSQL. Current official research confirms Render free APIs sleep
  after 15 idle minutes and Render free databases expire after 30 days. Supabase's free database has
  no fixed 30-day expiry, though a low-activity project can pause after seven days. Render must use
  Supabase's IPv4-compatible Session Pooler on port 5432, not the IPv6 direct endpoint.
- Added `render.yaml`, a portable production start script, exact API/frontend environment contracts,
  managed PostgreSQL URL normalization, HTTPS-only production CORS, and explicit docs/schema
  exposure via `EXPOSE_API_DOCS`.
- `/api/v1/health` now checks PostgreSQL and is the platform readiness path.
- The public demo helper uses `VITE_DEMO_EMAIL` and `VITE_DEMO_PASSWORD`; the local development
  fallback remains available only in Vite development mode. The frontend and backend deployment
  values must match. The public demo password must never be reused as a private credential.
- Added SPA rewrites, response-security headers, production metadata, a ClientFlow favicon, a
  provider guide in `deployment/README.md`, and PostgreSQL-backed GitHub Actions CI.
- Playwright accepts `PLAYWRIGHT_BASE_URL` plus `VITE_API_URL`; `npm run test:smoke:production`
  serially runs the complete MVP flow and nested-route/responsive checks against the public services
  with free-tier cold-start timeouts. Do not claim production verification using localhost results.
- `render.yaml` validates against Render's official schema. A disposable production rehearsal
  migrated a blank database to head, seeded/no-op seeded, authenticated, and returned 200 for
  database health, docs, and schema with exact CORS; the database was then removed.
- GitHub Actions run `37351674829` passed the PostgreSQL backend and frontend production-build jobs
  after the Supabase deployment documentation was pushed.

Next actions, in order:

1. The user has confirmed the Supabase account connection. Create `clientflow` in Singapore, copy
   the **Session pooler** port 5432 URL, and provide it only through Render's secret prompt (never
   in chat or Git).
2. The user has confirmed the Render account connection. Create the Blueprint from
   `AbrarUI12/Client_Flow`, then enter `DATABASE_URL`, `DEMO_USER_PASSWORD`, and the identical
   `VITE_DEMO_PASSWORD` when prompted.
3. Verify Render deploy logs, migration head, HTTPS health/docs/frontend, exact CORS, and
   direct refresh on every nested route.
4. Run the full production MVP smoke flow from `session.md`, record live URLs/evidence here and in
   `session.md`, mark Session 14 complete, commit, and push. Only then begin Session 15.

## Remaining roadmap after Session 13

- Session 14 — finish the account-bound deployment and public production verification listed above.
- Session 15 — Portfolio handoff: complete README, public links, architecture and ER diagrams,
  authorization/money/state-machine explanations, polished screenshots, 60-90 second demo plan,
  case study, clean-clone verification, and optional `v1.0.0` tag.

Refer to each full session section in `session.md` before starting; the bullets above do not replace
its detailed requirements and completion gates.

## Current verification baseline and known non-blockers

- Session 14 repository-preparation baseline:
  - Backend: Ruff clean and `134 passed` on PostgreSQL, deterministic across repeated runs, with
    the test database empty afterward. The suite covers authentication/route inventory, a tenant
    isolation matrix, archive rules, input safety, rollback, conflicts, row locks, the migration
    round trip with drift detection, and seed safety. Reverting each key fix makes its guard test
    fail.
  - Frontend: lint, `tsc -b`, and the production build are clean.
  - Browser: `10` Playwright tests pass. The new `e2e/mvp.spec.ts` runs the full MVP flow once and
    double-clicks submits to prove one record per action.
  - GitHub Actions: run `37335413206` passed the PostgreSQL backend and frontend production-build
    jobs for `39bcc0b`.
- Expected non-blocking warnings: Starlette TestClient warns about future `httpx2`; Vite warns that
  the main minified bundle exceeds 500 kB. Address bundle splitting during polish/hardening if it
  remains useful; neither warning currently breaks a gate.
- No real secrets belong in the repository. `.env` files, build output, Playwright artifacts,
  virtual environments, and `.tmp` are ignored.

## Handoff checklist for every future session

1. Read this file and the exact current section in `session.md`.
2. Check `git status`, recent log, branch, and remote before editing.
3. Confirm the previous pushed commit and baseline tests.
4. Finish only the current session, including error/empty/loading/mobile/ownership behavior that
   applies to it.
5. Test proportionally, including PostgreSQL for database-specific behavior and Playwright for the
   primary browser flow.
6. Update `session.md` status and this file's completed-history, WIP, next-actions, and baseline.
7. Commit and push the finished session to `origin/main`.
8. Confirm the tree is clean and the remote contains the commit before starting the next session.

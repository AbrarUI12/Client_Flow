# ClientFlow Agent Handoff

Last updated: 2026-10-05, after Session 11 verification and before its push.

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

PostgreSQL-specific tests require `TEST_DATABASE_URL`. On this workstation Docker is unavailable,
so an ignored portable PostgreSQL 17.11 installation exists under `.tmp/postgres-portable`, runs on
`127.0.0.1:55432`, and uses:

```text
postgresql+psycopg://postgres@127.0.0.1:55432/clientflow
```

The portable cluster can be checked or stopped with `pg_ctl.exe` in that folder. Do not commit the
`.tmp` directory. At this update PostgreSQL, Vite on port 5173, and Uvicorn on port 8000 are running,
but future sessions must verify process state rather than assuming it.

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
| 11 | Added deterministic screenshot-ready demo data, idempotent normal seed, isolated demo-only reset, production refusal, and tenant-preservation tests | `feat: add realistic repeatable demo data` |

Sessions 0-11 are marked implemented and verified in `session.md`. Sessions 0-10 are on
`origin/main`; Session 11 is the next commit/push at this handoff update.

## Important implemented behavior

### Authentication

- Bearer JWT access tokens live in `sessionStorage`, not persistent local storage.
- The central API client attaches auth and emits an unauthorized event on 401.
- Login errors do not distinguish unknown users from bad passwords.
- Every business route depends on the current active user.

### Leads

- All lead access is scoped by `owner_id`; foreign records return the same structured 404 as missing
  records.
- Archived leads disappear from normal detail and list queries.
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

## Next session: Session 12

Session 11 has cleared its full verification gate. Commit and push it, then start Session 12 from a
clean tree and confirmed remote boundary.

Session 12 objective: make the finished product visually coherent, responsive, accessible, and
presentation-ready without adding scope. Read the full Session 12 section in `session.md`. Audit and
standardize visual primitives and status meanings; add consistent success/error notifications,
pending protection, understandable business errors, consequential-action confirmations, and a
useful 404 page. Check every primary route at mobile/tablet/laptop/wide sizes, eliminate accidental
overflow, and keep actions findable. Complete keyboard/focus/dialog/label/contrast/document-title/
enlarged-text accessibility checks. Remove tutorial/placeholder wording, normalize terminology and
grammar, and ensure every empty state offers a next action.

## Remaining roadmap after Session 11

- Session 12 — UX/accessibility polish: shared visual primitives, notifications, confirmations,
  useful 404, all target breakpoints, keyboard/focus/dialog behavior, contrast, titles, enlarged
  text, and removal of all placeholder/tutorial content.
- Session 13 — Release hardening: complete ownership/business/security suite on PostgreSQL,
  deterministic isolation, frontend/build/browser gates, secret/CORS/logging/error review,
  transaction/duplicate/migration reliability review.
- Session 14 — Deployment: choose suitable current providers, managed PostgreSQL, HTTPS API/static
  frontend, exact production env/CORS, migrations and seed, SPA fallback, metadata/favicon, GitHub
  Actions, and full public production smoke test. Provider research must use current information.
- Session 15 — Portfolio handoff: complete README, public links, architecture and ER diagrams,
  authorization/money/state-machine explanations, polished screenshots, 60-90 second demo plan,
  case study, clean-clone verification, and optional `v1.0.0` tag.

Refer to each full session section in `session.md` before starting; the bullets above do not replace
its detailed requirements and completion gates.

## Current verification baseline and known non-blockers

- Session 11 baseline: backend Ruff clean; `40 passed` with all PostgreSQL integration tests enabled.
  An isolated PostgreSQL database also passed migration, empty seed, no-op repeat seed, modified-data
  reset, exact 30/8/21/12 restoration, other-owner preservation, and production-mode reset refusal.
  Frontend lint and production build are clean; all `7` Playwright workflows still pass.
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

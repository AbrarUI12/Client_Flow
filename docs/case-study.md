# ClientFlow engineering case study

## The business problem

A small service business rarely needs enterprise CRM complexity, but it still needs a dependable answer to four questions: Who is the prospect? What was quoted? What happens next? What is the pipeline worth?

In a spreadsheet-and-chat workflow, those answers drift apart. Price formulas can be overwritten, a follow-up can disappear in message history, and one person's customer data can leak into another workspace. ClientFlow was designed to make the smallest useful sales workflow coherent and trustworthy.

## Choosing the v1 boundary

The product boundary was intentionally narrow:

```text
authenticate → manage owned leads → quote accurately → follow up → measure → export
```

V1 includes leads, quotations, reminders, dashboard metrics, PDF/CSV exports, deterministic demo data, and responsive accessibility. It excludes teams, email delivery, invoices, payments, automation, custom pipelines, and third-party integrations. That boundary made it possible to harden the complete workflow instead of presenting many incomplete features.

## Data and authorization design

PostgreSQL is the source of truth. A user directly owns leads; quotations and follow-ups inherit ownership through their lead. Every business query applies that ownership predicate before returning or mutating a row. Foreign-owned and absent IDs are indistinguishable to the caller.

FastAPI routes share one request-scoped SQLAlchemy session. Successful database work commits before the success response is returned, while failures roll back. State-changing quotation and follow-up operations lock the current row so simultaneous requests cannot both win.

The database carries part of the safety model through foreign keys, enums, precision, uniqueness, indexes, and consistency checks. Alembic—not ORM auto-creation—is the schema deployment path.

## The most important implementation challenge

The hardest part was not drawing the screens; it was keeping one business event consistent across features.

Accepting a quotation illustrates the problem. It must validate the current quote state, reject archived or foreign data, prevent a concurrent reject from also succeeding, mark the quotation accepted, mark the lead won, commit both changes, and invalidate every affected browser view. A failure at any point must leave neither half applied.

The solution combines service-layer transition rules, PostgreSQL row locks, a single transaction, commit-before-response behavior, consistent query invalidation, and tests that deliberately race conflicting operations.

## Protecting quotation accuracy

The API never trusts totals submitted by the browser. It accepts quantities, unit prices, discount, and tax inputs, then derives every financial value with `Decimal`. PostgreSQL stores them as fixed-precision `NUMERIC`, and `ROUND_HALF_UP` is applied at explicit money boundaries.

The browser mirrors the policy with scaled integer arithmetic so its preview is useful, but the saved API response remains authoritative. Dashboard totals and generated PDFs use the stored server results. Tests cover rounding edges, multi-item totals, discounts, taxes, replacement edits, invalid values, and exported totals.

## How it was tested

The final backend suite contains 134 PostgreSQL tests. Each run rebuilds a dedicated `_test` schema from Alembic and encloses every test in an outer transaction that is rolled back. Coverage includes authentication, an ownership matrix, archived records, validation safety, money calculations, migrations, demo reset isolation, database failures, conflicts, and row locks.

Playwright exercises the real browser workflow: login, lead creation, quotation creation and transitions, PDF/CSV downloads, follow-ups, dashboard refresh, keyboard use, dialogs, 404 behavior, double-click safety, 200% text, and 390/768/1280/1600-pixel layouts. Static gates include Ruff, oxlint, TypeScript, and the Vite production build.

The public Render/Supabase deployment has a separate smoke suite. It verifies health, exact CORS behavior, authentication, all route patterns, the end-to-end MVP, binary exports, and responsive behavior against production.

## Result

ClientFlow is a complete, deployed portfolio application rather than a collection of disconnected CRUD pages. A reviewer can use the public demo, trace the architecture, reproduce the database from migrations, generate the dataset, run the verification suites, and inspect the exact behavior behind each visible state.

The implementation also produced reusable engineering patterns: server-authoritative financial calculations, ownership through parent relations, safe idempotent seeds, transaction-aware response timing, and browser mutation guards that are backed by database guarantees.

## What comes next for a real client

The first production discovery would determine whether ClientFlow should grow around collaboration, delivery, or finance. Likely v2 work would include:

- Team workspaces, invitations, assignments, roles, and an immutable activity history.
- Password recovery, refresh-session rotation, MFA, rate limiting, and account onboarding.
- Branded quote templates, email delivery, customer approval links, invoices, and payment tracking.
- Custom stages, tags, CSV import, saved filters, conversion analytics, and reminder notifications.
- Background jobs, object storage, structured observability, backup drills, and paid always-on hosting.

Those features should build on the existing ownership, transaction, precision, and test boundaries rather than weakening them.

## Review links

- [Live application](https://clientflow-web-abrarui12-kocw.onrender.com)
- [Interactive API documentation](https://clientflow-api-abrarui12-kocw.onrender.com/docs)
- [Architecture and data design](architecture.md)
- [Timed demo script](demo-script.md)
- [Local setup and verification](../README.md)


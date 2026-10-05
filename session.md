# ClientFlow v1 — Detailed Build Sessions

## 1. Purpose of This Document

This document converts the approved ClientFlow v1 design into a sequence of focused implementation sessions.

The source product specification is:

```text
ClientFlow_v1_Full_Project_Design.md
```

Each session must leave the project in a working, reviewable state. A session is complete only when its verification gate passes. Do not continue to the next session while the current session has known blocking errors.

The sessions are intentionally organized around vertical progress:

```text
Foundation
    ↓
Database
    ↓
Authentication
    ↓
Leads
    ↓
Quotations
    ↓
Follow-ups
    ↓
Dashboard
    ↓
Exports
    ↓
Quality and deployment
```

---

## 2. Approved v1 Scope

ClientFlow is a full-stack CRM-lite application for an owner or salesperson at a small service business.

The v1 product must support this complete workflow:

```text
Login as the demo user
        ↓
View the dashboard
        ↓
Create and qualify a lead
        ↓
Create a quotation for that lead
        ↓
Add line items, discount, and tax
        ↓
Save and mark the quotation as sent
        ↓
Download the quotation PDF
        ↓
Schedule and complete a follow-up
        ↓
Accept the quotation
        ↓
Automatically mark the lead as won
        ↓
Export leads to CSV
```

### Included

- Demo-user authentication
- Ownership-based authorization
- Dashboard metrics and operational lists
- Lead creation, listing, searching, filtering, editing, and archiving
- Quotation creation, draft editing, status changes, and accurate calculations
- Quotation PDF generation
- Follow-up creation, categorization, and completion
- Lead CSV export
- Responsive desktop and mobile interface
- Critical automated tests
- Repeatable demo data
- Production deployment
- Portfolio documentation and evidence

### Excluded

- Public registration
- Password recovery
- Staff roles and complex permissions
- Multiple businesses inside one account
- Email or WhatsApp sending
- Calendar synchronization
- Payment processing
- Subscriptions
- Inventory and accounting
- AI features
- Real-time sockets
- Native mobile applications

Requests for excluded features should be recorded as possible v2 work rather than added during v1 implementation.

---

## 3. Locked Architecture Decisions

### Frontend

| Concern | Decision |
|---|---|
| Framework | React with TypeScript |
| Build tool | Vite |
| Styling | Tailwind CSS |
| Routing | React Router |
| Server state | TanStack Query |
| Forms | React Hook Form |
| Frontend validation | Zod |
| Icons | A consistent SVG icon library |
| API format | JSON over HTTPS |

The frontend will be organized primarily by product feature instead of placing all code in large generic folders.

Suggested structure:

```text
frontend/
├── src/
│   ├── app/
│   │   ├── App.tsx
│   │   ├── router.tsx
│   │   └── queryClient.ts
│   ├── components/
│   │   ├── layout/
│   │   └── ui/
│   ├── features/
│   │   ├── auth/
│   │   ├── dashboard/
│   │   ├── leads/
│   │   ├── quotations/
│   │   └── followups/
│   ├── lib/
│   │   ├── apiClient.ts
│   │   ├── errors.ts
│   │   └── formatting.ts
│   ├── types/
│   ├── main.tsx
│   └── index.css
├── .env.example
├── package.json
└── vite.config.ts
```

### Backend

| Concern | Decision |
|---|---|
| API framework | FastAPI |
| Validation | Pydantic |
| ORM | SQLAlchemy 2.x |
| Database access | Synchronous PostgreSQL sessions |
| Database | PostgreSQL |
| Migrations | Alembic |
| Authentication | JWT bearer access token |
| Password hashing | Argon2 |
| Money | Python `Decimal` and PostgreSQL `NUMERIC` |
| PDF | ReportLab |
| CSV | Python standard-library CSV support |
| Backend tests | Pytest |

Suggested structure:

```text
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── router.py
│   │       ├── auth.py
│   │       ├── dashboard.py
│   │       ├── leads.py
│   │       ├── quotations.py
│   │       └── followups.py
│   ├── core/
│   │   ├── config.py
│   │   ├── errors.py
│   │   └── security.py
│   ├── db/
│   │   ├── base.py
│   │   └── session.py
│   ├── dependencies/
│   │   ├── auth.py
│   │   └── database.py
│   ├── models/
│   ├── schemas/
│   ├── services/
│   ├── scripts/
│   └── main.py
├── alembic/
├── tests/
├── .env.example
├── alembic.ini
└── pyproject.toml
```

### Request flow

```text
React form or action
        ↓
Frontend usability validation
        ↓
Authenticated API request
        ↓
Pydantic validation
        ↓
Ownership check
        ↓
Service and business rules
        ↓
SQLAlchemy transaction
        ↓
PostgreSQL
        ↓
Structured response
        ↓
Frontend query refresh and feedback
```

Backend validation and calculations are authoritative. Frontend validation exists to provide faster feedback, not to establish trust.

---

## 4. Locked Product and Data Decisions

### Authentication

- There is no public registration screen or endpoint in v1.
- A demo user is created by a seed command.
- Login returns a time-limited JWT access token.
- The frontend stores the token in `sessionStorage`.
- The frontend sends the token with the `Authorization: Bearer ...` header.
- A `401 Unauthorized` response clears the local session and returns the user to `/login`.
- Logout clears the token on the frontend.
- A stateless JWT is not immediately revoked on logout; it naturally expires after its configured lifetime.

### Ownership

Every business record belongs to a user through its lead relationship.

Ownership must be applied inside database queries. For example:

```text
lead.id = requested_id
AND
lead.owner_id = current_user.id
```

The same principle applies to:

- Lead details and updates
- Quotation details and updates
- Quotation PDFs
- Follow-ups
- Dashboard calculations
- CSV exports

### Business profile

The user record will also contain the information needed for dates, currency, and quotation headers:

- `business_name`
- `business_address`
- `business_phone`
- `currency_code`
- `timezone`

These values are seeded in v1. A profile/settings screen is not part of the first release.

### Money

- Do not use Python `float` for persisted or authoritative monetary calculations.
- Store currency values as PostgreSQL `NUMERIC`.
- Use Python `Decimal` in backend code.
- Return monetary values as JSON strings when necessary to preserve exact decimal values.
- Quantize final currency values consistently to two decimal places.
- The browser may display a live preview, but saved totals always come from the backend.

### Quotation numbering

Quotation database IDs are UUIDs. A PostgreSQL sequence generates human-readable quotation numbers:

```text
Q-2026-00017
```

Sequence gaps are acceptable and must not be treated as data corruption.

### Quotation state transitions

```text
DRAFT → SENT → ACCEPTED
             ↘ REJECTED
```

- Only a draft can be edited.
- An accepted or rejected quotation is final in v1.
- Accepting a quotation and setting its lead to `WON` occur inside one transaction.
- Rejecting a quotation does not automatically set the lead to `LOST`.
- Invalid transitions return a structured business error.

### Dates and timezones

- Store timestamps as timezone-aware UTC values.
- Display them in the authenticated user's configured timezone.
- Determine overdue, today, and upcoming status using the user's timezone.
- Record follow-up completion with `completed_at`.

### Archiving

- Leads are archived rather than permanently deleted.
- Archived leads are hidden from normal lists, dashboard metrics, and default exports.
- Related quotations and follow-ups remain stored.
- Permanent deletion is outside v1.

---

## 5. Visual and Interaction Direction

ClientFlow should look like a real operational business application rather than a generic tutorial dashboard.

### Visual thesis

- Deep navy application sidebar
- Cool neutral page background
- White or subtly elevated working surfaces
- Strong blue for primary actions and navigation state
- Emerald for positive completion states
- Amber for pending or due states
- Red for destructive, lost, rejected, and overdue states
- Clear type hierarchy with readable 16px body text
- Compact tables with generous interactive target sizes
- Restrained borders, shadows, and motion

### Desktop shell

```text
┌────────────────┬─────────────────────────────────────────────┐
│ ClientFlow     │ Page title                    Primary action │
│                ├─────────────────────────────────────────────┤
│ Dashboard      │                                             │
│ Leads          │              Page content                   │
│ Quotations     │                                             │
│ Follow-ups     │                                             │
│                │                                             │
│ User / Logout  │                                             │
└────────────────┴─────────────────────────────────────────────┘
```

### Mobile shell

- Replace the permanent sidebar with a menu drawer.
- Keep the page title and essential action visible.
- Convert wide record tables into stacked cards when horizontal scrolling would make the main workflow difficult.
- Use full-width form controls and touch-friendly actions.

### Required UI states

Every primary page must deliberately support:

- Loading
- Empty
- Error
- Success
- Unauthorized session
- Missing record

Blank tables and silent failures are not acceptable final states.

---

# Session 0 — Specification and Architecture Lock

## Objective

Confirm exactly what will be built before creating application code.

## Work

- Review the complete product specification.
- Confirm the v1 workflow and excluded features.
- Confirm the frontend, backend, database, and deployment architecture.
- Add the missing quotations list and detail experience.
- Define authentication storage and logout behavior.
- Define money, quotation numbering, timezone, and ownership rules.
- Divide the project into implementation sessions.

## Deliverables

- Approved product design document
- This session execution plan
- A stable definition of v1 completion

## Verification gate

- The user approves the plan.
- There are no unresolved choices that would significantly change the repository structure or data model.

## Status

```text
APPROVED AND COMPLETE — 2026-10-04
```

---

# Session 1 — Repository and Development Foundation

## Objective

Create a reproducible full-stack workspace in which the frontend, backend, and PostgreSQL can communicate.

## Theory

This session proves the delivery pipeline before product features are introduced. A health request passing from the browser environment to FastAPI prevents later debugging from mixing infrastructure problems with business-logic problems.

## Work

### Repository

- Initialize Git if the workspace is not already a repository.
- Add `backend/` and `frontend/` directories.
- Create a root `.gitignore`.
- Add a short root `README.md` with local setup placeholders.
- Add a root development database configuration, preferably Docker Compose for reproducibility.

### Backend foundation

- Create the Python project configuration.
- Install FastAPI, the ASGI server, Pydantic settings, SQLAlchemy, PostgreSQL driver, Alembic, JWT support, Argon2 support, ReportLab, and Pytest.
- Create the application entry point.
- Create a versioned API router.
- Add `GET /api/v1/health`.
- Create typed environment configuration.
- Configure allowed development CORS origin explicitly.
- Add `backend/.env.example` without real credentials.

### Frontend foundation

- Create the React, TypeScript, and Vite application.
- Configure Tailwind CSS.
- Add routing and query-client foundations.
- Replace starter/demo content with a minimal ClientFlow connection screen.
- Add `frontend/.env.example` containing `VITE_API_URL`.
- Call the health endpoint and show a simple connected or unavailable result.

## Expected files

```text
README.md
.gitignore
docker-compose.yml
backend/
frontend/
```

## Verification

- Start PostgreSQL.
- Start FastAPI.
- Start the Vite development server.
- Request `/api/v1/health` directly.
- Confirm the frontend can request the same endpoint.
- Confirm the frontend production build completes.

## Completion gate

```text
React application loads
        +
GET /api/v1/health returns HTTP 200
        +
Browser-to-API request succeeds
```

## Suggested commit

```text
chore: establish full-stack project foundation
```

## Status

```text
IMPLEMENTED AND VERIFIED — 2026-10-05
```

The API tests, Python lint, frontend lint, production build, direct health request, configured CORS response, and browser-rendered connection state pass. The Docker Compose configuration is present and parses successfully; starting PostgreSQL locally remains an environment prerequisite because Docker and PostgreSQL are not installed on the verification machine.

---

# Session 2 — Database Models, Migrations, and Seed Foundation

## Objective

Create the complete relational database foundation before implementing feature APIs.

## Theory

The database is the long-lived source of truth. Relationships, constraints, indexes, nullability, precision, and cascade behavior should be intentional before routes depend on them.

## Work

### Database connection

- Add the SQLAlchemy engine and session factory.
- Provide one database session per request.
- Configure safe commit, rollback, and close behavior.
- Connect Alembic to application metadata.

### Models

Create:

- `User`
- `Lead`
- `Quotation`
- `QuotationItem`
- `FollowUp`

### Important fields

#### User

- UUID ID
- Email
- Full name
- Password hash
- Active flag
- Business name, address, and phone
- Currency code
- Timezone
- Created and updated timestamps

#### Lead

- UUID ID
- Owner foreign key
- Contact and company information
- Source and status
- Estimated value using `NUMERIC`
- Notes
- Archive flag
- Created and updated timestamps

#### Quotation

- UUID ID
- Lead foreign key
- Human-readable quote number
- Status
- Issue and validity dates
- Subtotal, discount, tax, and total fields
- Notes
- Relevant status timestamps
- Created and updated timestamps

#### Quotation item

- UUID ID
- Quotation foreign key
- Description
- Decimal quantity
- Unit price
- Line total
- Sort order

#### Follow-up

- UUID ID
- Lead foreign key
- Due timestamp
- Note
- Completion flag and timestamp
- Created and updated timestamps

### Constraints and indexes

- Unique normalized user email
- Foreign-key constraints
- Nonnegative monetary database checks where practical
- Useful indexes for owner, status, created date, due date, and archive state
- Cascade quotation-item deletion with its quotation
- Consistent enum storage strategy

### Migration

- Initialize Alembic.
- Generate the initial migration.
- Manually review the generated migration.
- Apply it to an empty database.
- Downgrade and upgrade once to verify reversibility.

### Seed foundation

- Add a script framework for creating the demo user.
- Read seed credentials from controlled configuration or documented development defaults.
- Make user creation idempotent.

## Verification

- Build an empty database entirely through Alembic.
- Confirm all tables, indexes, constraints, and the quote-number sequence exist.
- Run the seed command twice without creating duplicate users.

## Completion gate

```text
Empty PostgreSQL database
        ↓
Alembic upgrade
        ↓
Complete valid schema
        ↓
Idempotent demo-user seed
```

## Suggested commit

```text
feat: add database models and initial migration
```

## Status

```text
IMPLEMENTED AND VERIFIED — 2026-10-05
```

Verified against PostgreSQL 17.11: the initial migration creates five application tables, 24 application indexes, 30 application constraints, and the quotation-number sequence. Alembic reports no model/migration drift; downgrade removes every application table and the sequence; re-upgrade succeeds; and the demo seed creates one user then safely reports that it already exists on repeated execution.

---

# Session 3 — Authentication and Protected Application Shell

## Objective

Complete authentication end to end and establish the protected application layout.

## Theory

Authentication proves identity. Authorization decides which records that identity may use. This session implements identity; ownership authorization is reinforced in every later resource session.

## Backend work

- Add password hashing and verification utilities.
- Add JWT creation and validation.
- Define the access-token expiry setting.
- Implement `POST /api/v1/auth/login`.
- Implement `GET /api/v1/auth/me`.
- Implement the current-user dependency.
- Reject inactive users.
- Return the same safe login error for unknown email and incorrect password.
- Add structured authentication errors.
- Keep or add `POST /api/v1/auth/logout` as a semantic 204 response while documenting stateless-token behavior.

## Frontend work

- Create the login page.
- Add email, password, password visibility, pending, and error states.
- Store the token in `sessionStorage` after successful login.
- Add the token to authenticated API requests.
- Load the current user on application startup.
- Clear the session and redirect on `401`.
- Add protected-route handling.
- Create the responsive application shell with sidebar/navigation.
- Add a temporary authenticated dashboard placeholder.
- Implement logout.

## Required tests

- Correct password logs in.
- Incorrect password is rejected.
- Unknown user is rejected safely.
- Anonymous access to `/auth/me` is rejected.
- Valid token returns the current user.
- Invalid or expired token is rejected.
- Password hashes are not returned by APIs.

## Completion gate

```text
Login page
    ↓
Valid demo credentials
    ↓
Protected ClientFlow shell
    ↓
Refresh keeps the tab session
    ↓
Logout returns to login
```

## Suggested commit

```text
feat: implement JWT authentication flow
```

## Status

```text
IMPLEMENTED AND VERIFIED — 2026-10-05
```

Backend authentication tests cover valid, invalid, unknown, inactive, anonymous, expired-token, current-user, and logout behavior. A real-browser PostgreSQL-backed test verifies demo login, protected-shell access, `sessionStorage` persistence after refresh, and logout redirection.

---

# Session 4 — Lead API and Ownership Enforcement

## Objective

Implement the complete lead backend, including search, filtering, pagination, archiving, and user isolation.

## Theory

Leads are the aggregate root for quotations and follow-ups. Their API and ownership rules must be stable before dependent features are added.

## Backend work

- Create lead request and response schemas.
- Normalize and validate optional contact fields.
- Validate contact name length.
- Validate supplied emails.
- Validate nonnegative estimated value.
- Define lead status and source values.
- Implement:

```text
POST   /api/v1/leads
GET    /api/v1/leads
GET    /api/v1/leads/{id}
PATCH  /api/v1/leads/{id}
POST   /api/v1/leads/{id}/archive
```

- Add page and page-size validation.
- Add deterministic default ordering.
- Add case-insensitive search across contact, company, email, and phone.
- Add status and source filters.
- Exclude archived leads by default.
- Return pagination metadata.
- Return not found for resources the user does not own without revealing that another user's record exists.

## Required tests

- Create a valid lead.
- Reject invalid lead data.
- List only the current user's leads.
- Search by contact and company.
- Filter by status and source.
- Paginate with stable results.
- Update an owned lead.
- Archive an owned lead.
- Exclude archived leads from normal results.
- Prevent User A from viewing, updating, or archiving User B's lead.

## Completion gate

The complete lead API passes tests, including cross-user authorization tests.

## Suggested commit

```text
feat: implement authorized lead management API
```

## Status

```text
IMPLEMENTED AND VERIFIED — 2026-10-05
```

The lead API passes validation, normalization, search, filtering, deterministic pagination, update, archive, archived-exclusion, and cross-user isolation tests. Another user's lead returns the same structured `404` for view, update, and archive attempts.

---

# Session 5 — Lead User Experience

## Objective

Deliver the first complete business-facing vertical slice: create, find, edit, view, and archive a lead.

## Pages

```text
/leads
/leads/new
/leads/:id
/leads/:id/edit
```

## Work

### Lead list

- Add the page heading and `Add Lead` action.
- Add debounced search.
- Add status and source filters.
- Synchronize useful filters with the URL query string.
- Add pagination.
- Add loading skeletons.
- Add an actionable empty state.
- Add error and retry states.
- Show status badges consistently.
- Use a table on desktop and record cards on narrow screens.

### Lead form

- Build reusable create/edit form fields.
- Implement frontend validation matching backend expectations.
- Preserve user input when the API returns an error.
- Show field and general errors clearly.
- Prevent duplicate submission.
- Navigate to the saved lead after successful creation.

### Lead detail

- Show contact, company, status, source, estimated value, and notes.
- Reserve sections for quotations and follow-ups.
- Add edit, create quotation, and add follow-up actions.
- Add an archive confirmation.
- Handle missing or inaccessible leads.

### Query behavior

- Define stable query keys.
- Refresh list and detail data after changes.
- Avoid unnecessary full-page reloads.

## Verification

- Create a lead from the UI.
- Find it using search.
- Filter it by status.
- Edit its information.
- Open its detail page.
- Archive it and confirm it disappears from the normal list.
- Repeat primary checks at mobile width.

## Completion gate

```text
Login
  → Add lead
  → See it in the list
  → Search/filter it
  → Edit it
  → Open details
  → Archive it
```

## Suggested commit

```text
feat: add complete lead management interface
```

## Status

```text
IMPLEMENTED AND VERIFIED — 2026-10-05
```

The complete create, search, filter, edit, detail, and archive journey passes real-browser tests against PostgreSQL at desktop and mobile widths. The lead list also includes URL-synchronized filters, debounced search, pagination, loading, empty, retry, responsive table/card states, and stable query-cache updates.

---

# Session 6 — Quotation Engine and API

## Objective

Implement accurate quotation calculations, persistence, ownership, numbering, and state transitions.

## Theory

Quotation values are financial data. The backend must ignore client-supplied totals and calculate them from validated quantities, prices, discounts, and tax rates.

## Calculation rules

```text
line_total = quantity × unit_price

subtotal = sum(line_total)

discount_amount = subtotal × discount_percent / 100

discounted_subtotal = subtotal - discount_amount

tax_amount = discounted_subtotal × tax_percent / 100

total = discounted_subtotal + tax_amount
```

All values must follow one documented decimal rounding policy.

## Backend work

- Create quotation and item schemas.
- Create the quotation calculation service.
- Require at least one item.
- Require nonblank descriptions.
- Require quantity greater than zero.
- Require unit price of zero or more.
- Limit discount and tax percentages to 0–100.
- Require validity date on or after issue date.
- Generate a quote number safely.
- Save quotation and items in one transaction.
- Replace draft items transactionally during a draft edit.
- Implement:

```text
POST  /api/v1/leads/{lead_id}/quotations
GET   /api/v1/leads/{lead_id}/quotations
GET   /api/v1/quotations
GET   /api/v1/quotations/{id}
PATCH /api/v1/quotations/{id}
PATCH /api/v1/quotations/{id}/status
```

- Add quotation list search, status filtering, and pagination.
- Apply ownership through the related lead.
- Reject edits to non-draft quotations.
- Enforce legal status transitions.
- Update the lead to `WON` inside the same transaction when a quote becomes accepted.

## Required tests

- Correct line totals.
- Correct subtotal.
- Correct discount.
- Tax applied after discount.
- Correct final total and rounding.
- Client-supplied totals are ignored or not accepted.
- At least one item is required.
- Negative price and zero/negative quantity are rejected.
- Invalid date ranges are rejected.
- Unique quote numbers are generated.
- Draft quote can be edited.
- Sent quote cannot be edited.
- Invalid transitions are rejected.
- Accepting a quote marks its lead won.
- Rejecting a quote does not mark its lead lost.
- Cross-user access is blocked.

## Completion gate

Quotation calculations and all business-state tests pass against PostgreSQL.

## Suggested commit

```text
feat: add quotation calculation and workflow API
```

## Status

```text
IMPLEMENTED AND VERIFIED — 2026-10-05
```

The quotation API calculates all monetary values with documented decimal rounding, generates PostgreSQL sequence-backed quote numbers, persists item replacement atomically, filters and paginates owned records, and enforces the draft/sent/accepted/rejected transition graph. The complete test suite passes with PostgreSQL integration enabled, including acceptance updating the related lead to won and cross-user access returning hidden-resource responses.

---

# Session 7 — Quotation Builder, List, and Detail Experience

## Objective

Allow the user to build, review, edit, and progress quotations from the browser.

## Pages

```text
/quotations
/quotations/:id
/quotations/:id/edit
/leads/:leadId/quotes/new
```

## Work

### Quotation builder

- Show the selected client clearly.
- Add issue date and valid-until fields.
- Add dynamic line items.
- Allow line-item reordering or stable manual ordering.
- Prevent removal of the final required item without a clear empty-row replacement.
- Add discount and tax inputs.
- Show a decimal-safe calculation preview.
- Add quotation notes.
- Implement save draft.
- Implement save and mark sent.
- Reconcile the preview with authoritative totals returned by the backend.
- Show validation errors beside the affected field or item.

### Quotation list

- Add search.
- Add status filter.
- Add pagination.
- Show quote number, client, dates, total, and status.
- Provide useful loading, empty, and error states.
- Use responsive cards when necessary.

### Quotation detail

- Show business identity, customer identity, items, calculations, dates, notes, and status.
- Show edit only for drafts.
- Add legal status actions based on the current status.
- Add a PDF action placeholder for Session 10.
- Link back to the related lead.

### Lead integration

- Show quotation summaries on the lead detail page.
- Refresh lead information when an accepted quote changes its status to won.

## Verification

- Create a three-item quotation.
- Apply a discount and tax.
- Confirm the live preview.
- Save it as a draft.
- Reopen and edit it.
- Mark it sent.
- Confirm editing is no longer offered.
- Mark it accepted and verify the lead becomes won.

## Completion gate

The complete lead-to-accepted-quotation workflow works through the user interface.

## Suggested commit

```text
feat: build quotation management experience
```

## Status

```text
IMPLEMENTED AND VERIFIED — 2026-10-05
```

The lead-to-accepted-quotation workflow passes a real-browser PostgreSQL-backed test. The UI includes an exact-decimal three-item preview, reorderable rows, draft editing, save-and-send behavior, authoritative detail totals, responsive search/filter/list states, legal status actions, business and customer identity, lead quotation summaries, and automatic lead refresh to won after acceptance.

---

# Session 8 — Follow-up Workflow

## Objective

Add time-based follow-up management from lead creation through completion.

## Backend work

- Create follow-up request and response schemas.
- Implement:

```text
POST  /api/v1/leads/{id}/follow-ups
GET   /api/v1/follow-ups
PATCH /api/v1/follow-ups/{id}
PATCH /api/v1/follow-ups/{id}/complete
```

- Require a nonblank note.
- Require a due date and time.
- Add filters for overdue, today, upcoming, and completed.
- Perform classification in the user's timezone.
- Define deterministic ordering for each group.
- Record `completed_at` when completed.
- Decide and test idempotent completion behavior.
- Apply ownership through the related lead.

## Frontend work

- Add an accessible add-follow-up dialog from the lead detail page.
- Show a lead's follow-ups on its detail page.
- Build `/follow-ups` with sections for overdue, today, upcoming, and completed.
- Link each record back to its lead.
- Add complete actions with immediate feedback.
- Add editing for incomplete follow-ups.
- Handle empty sections without unnecessary visual noise.
- Refresh affected lead, follow-up, and later dashboard queries.

## Required tests

- Create a valid follow-up.
- Reject missing note or due date.
- Classify overdue, today, and upcoming correctly.
- Complete a follow-up and record completion time.
- Prevent cross-user access.

## Completion gate

```text
Lead detail
  → Add follow-up
  → See it in the correct date group
  → Complete it
  → See completion recorded
```

## Suggested commit

```text
feat: add follow-up scheduling and completion
```

## Status

```text
IMPLEMENTED AND VERIFIED — 2026-10-05
```

Follow-ups can be created and edited from an accessible lead-detail dialog, are classified into deterministic overdue, today, upcoming, and completed groups in the user's timezone, and can be completed with immediate query refresh. Completion is idempotent and preserves its original timestamp. Validation, ownership, PostgreSQL timezone grouping, desktop behavior, and the mobile completion flow are covered by automated tests.

---

# Session 9 — Dashboard Aggregation and UI

## Objective

Build a strong operational dashboard using real application data.

## Theory

The dashboard is a read model. It summarizes existing records but must follow the same ownership, archive, status, money, and timezone rules as the underlying features.

## Backend work

- Implement `GET /api/v1/dashboard/summary`.
- Return:
  - Total non-archived leads
  - Open quotation count
  - Open quotation value
  - Overdue follow-up count
  - Pipeline count by lead status
  - Upcoming and overdue follow-up rows
  - Recent lead rows
- Define exactly which quote statuses count as open.
- Exclude archived leads consistently.
- Apply user ownership to every aggregate.
- Keep the dashboard to one primary API request.

## Frontend work

- Replace the dashboard placeholder.
- Add four metric cards.
- Add a clear numeric lead pipeline.
- Add upcoming and overdue follow-ups.
- Add recent leads.
- Add links to corresponding working pages.
- Use clear numbers before adding optional chart decoration.
- Add loading skeletons that preserve the page layout.
- Add useful empty and error states.
- Verify the first viewport works at common laptop widths.

## Required tests

- Aggregate only the current user's records.
- Exclude archived leads.
- Calculate open quote value accurately.
- Count overdue follow-ups using the user's timezone.
- Return correctly ordered recent leads and follow-ups.

## Completion gate

Changes made to leads, quotations, and follow-ups are accurately reflected on the dashboard.

## Suggested commit

```text
feat: add operational dashboard summary
```

## Status

```text
IMPLEMENTED AND VERIFIED — 2026-10-05
```

The dashboard uses one owned summary request for four metrics, the complete numeric lead pipeline, recent leads, and ordered overdue/upcoming reminders. Draft and sent quotations are explicitly counted as open, archived-lead data is excluded throughout, and overdue boundaries use the user's timezone. Ownership, aggregation accuracy, PostgreSQL behavior, data refresh, laptop layout, and mobile rendering are covered by automated tests.

---

# Session 10 — PDF and CSV Exports

## Objective

Generate professional quotation PDFs and safe, useful lead CSV files.

## Quotation PDF

- Implement `GET /api/v1/quotations/{id}/pdf`.
- Verify ownership before rendering.
- Use business profile fields for the document header.
- Include quote number, issue date, validity date, and status where appropriate.
- Include client information.
- Include all ordered items.
- Include subtotal, discount, tax, and total.
- Include notes when present.
- Use a professional one-page layout when the content fits.
- Support page breaks for longer quotations.
- Return an appropriate PDF content type and filename.
- Add the working download action to quotation detail.

## Lead CSV

- Implement `GET /api/v1/leads/export`.
- Export only the authenticated user's non-archived leads by default.
- Use a stable column order.
- Use human-readable status and dates.
- Preserve accurate decimal values.
- Quote and escape CSV values correctly.
- Protect spreadsheet users from formula injection in cells beginning with dangerous formula characters.
- Return an appropriate CSV content type and filename.
- Connect the export action on the lead list.

## Verification

- Download and open a quotation PDF.
- Confirm the PDF matches database totals.
- Test a quote containing enough items to cause a page break.
- Download and open the CSV in spreadsheet software.
- Confirm commas, quotes, Unicode, new lines, and potentially dangerous formula-like values are handled safely.
- Confirm cross-user export and PDF access are blocked.

## Completion gate

Both exports download successfully, contain correct information, and enforce ownership.

## Suggested commit

```text
feat: add quotation PDF and lead CSV exports
```

## Status

```text
IMPLEMENTED AND VERIFIED — 2026-10-05
```

Owned quotation PDFs now include business and client identity, dates and status, every ordered
item, server-authoritative totals, optional notes, page numbers, and automatic multi-page table
splitting. Lead CSV downloads use deterministic active-owner ordering, stable human-readable
columns, timezone-local dates, exact decimals, UTF-8 spreadsheet compatibility, standards-based
escaping, and formula-injection neutralization. Content, filenames, authentication, ownership,
long-document pagination, desktop download behavior, and mobile action visibility are automated.

---

# Session 11 — Complete Demo Dataset and Reset Workflow

## Objective

Create realistic, repeatable data for development, screenshots, demonstrations, and public portfolio review.

## Work

- Expand the seed command to create:
  - One demo user
  - Approximately 25–40 leads
  - All lead statuses
  - Several lead sources
  - Approximately eight quotations
  - Draft, sent, accepted, and rejected examples
  - At least 15 quotation items
  - Approximately 12 follow-ups
  - Overdue, today, upcoming, and completed examples
- Use fictional names, companies, phone numbers, and email addresses.
- Ensure dates are relative enough to remain useful when reseeded.
- Make the seed deterministic enough for screenshots and tests.
- Add an explicit reset mode that removes and recreates only the demo user's business data.
- Protect production reset behavior from accidental execution.
- Document how to run normal seed and reset seed operations.

## Verification

- Seed an empty database.
- Run the normal seed again and confirm it is idempotent.
- Modify demo data.
- Run the reset workflow.
- Confirm the application returns to its expected screenshot-ready state.
- Confirm no non-demo user's data is touched.

## Completion gate

One command can safely prepare a complete demo environment.

## Suggested commit

```text
feat: add realistic repeatable demo data
```

## Status

```text
IMPLEMENTED AND VERIFIED — 2026-10-05
```

The seed command now prepares 30 fictional leads across every status and all configured source
types, eight quotations across every quotation state with 21 calculated items, and 12 relative
follow-ups evenly covering overdue, today, upcoming, and completed. Stable UUIDs make normal seed
idempotent. `--reset` atomically replaces only the demo user's business records, preserves the user
account and other tenants, and is refused in production. Empty-database migration/seed, repeat seed,
modified-data restoration, tenant isolation, and production refusal pass on isolated PostgreSQL.

---

# Session 12 — UX Polish, Responsive Design, and Accessibility

## Objective

Make the complete application coherent, responsive, accessible, and presentation-ready without adding new product scope.

## Work

### Design system consistency

- Finalize color, spacing, typography, radius, border, and shadow tokens.
- Standardize buttons, inputs, selects, badges, tables, cards, dialogs, and notifications.
- Keep status meanings consistent across all screens.
- Use icons only when they improve recognition.

### Feedback and safety

- Add success and error notifications.
- Add confirmation dialogs for archive and other consequential actions.
- Disable repeated submissions while a request is pending.
- Preserve form input after recoverable failures.
- Make server business errors understandable.
- Add a useful 404 page.

### Responsive behavior

- Check login, dashboard, lists, forms, details, builder, and follow-ups at mobile, tablet, laptop, and wide-desktop sizes.
- Eliminate unintended horizontal scrolling.
- Ensure the mobile menu is keyboard and touch accessible.
- Ensure important actions remain easy to find.

### Accessibility

- Use semantic headings and landmarks.
- Connect labels, inputs, descriptions, and errors.
- Verify keyboard navigation and visible focus.
- Ensure dialogs manage focus correctly.
- Ensure status is not communicated by color alone.
- Check contrast.
- Add meaningful document titles.
- Add accessible names to icon-only buttons.
- Verify content remains usable when text is enlarged.

### Content review

- Remove placeholder and tutorial language.
- Use consistent terms for leads, quotations, and follow-ups.
- Check grammar and formatting.
- Confirm every empty state tells the user what they can do next.

## Verification

- Keyboard-only walkthrough of the primary flow.
- Mobile-width walkthrough of the primary flow.
- Text enlargement check.
- No blank or unexplained error/empty pages.
- No starter branding or placeholder content remains.

## Completion gate

Every primary route is coherent and usable on desktop and mobile with keyboard-accessible interactions.

## Suggested commit

```text
feat: polish responsive and accessible user experience
```

## Status

```text
IMPLEMENTED AND VERIFIED — 2026-10-05
```

ClientFlow now has shared live-region notifications, native focus-managed confirmation and
navigation dialogs, irreversible quotation safeguards, linked field errors, stronger focus and
reduced-motion styles, meaningful route titles, and a useful authenticated 404 page. Tutorial copy,
fake notification UI, placeholder components, and starter assets were removed. Automated keyboard
activation, focus return, dialog initial focus, 200% text, and no-overflow checks pass across
390/768/1280/1600-pixel layouts; all primary desktop/mobile workflows and visual QA also pass.

---

# Session 13 — Testing, Security, and Release Hardening

## Objective

Prove the critical business behavior and eliminate release-blocking security or reliability problems.

## Backend test suite

Complete or confirm tests for:

- Authentication success and failure
- Anonymous endpoint rejection
- Ownership across all resource types
- Lead validation and lifecycle
- Lead search, filters, pagination, and archive behavior
- Quotation arithmetic and rounding
- Quotation edit and state-transition rules
- Accepted quote updating its lead atomically
- Follow-up timezone classification and completion
- Dashboard ownership and aggregate accuracy
- PDF and CSV authorization

### Test database

- Run integration tests against PostgreSQL rather than substituting SQLite for database-specific behavior.
- Isolate tests through rollback, truncation, or per-test database strategy.
- Keep test results deterministic.

## Frontend checks

- Run TypeScript type checking.
- Run the production build.
- Add focused component tests only where they protect meaningful behavior.
- Add one browser-level happy-path test covering the most valuable workflow where practical.

## Security review

- Confirm no secrets are committed.
- Confirm CORS is explicit.
- Confirm every protected route uses authentication.
- Confirm every record query applies ownership.
- Confirm login errors do not reveal registered emails.
- Confirm passwords are Argon2 hashes.
- Confirm sensitive values are not logged.
- Confirm UUID input is validated safely.
- Confirm CSV formula injection is handled.
- Confirm downloadable files cannot be fetched across accounts.
- Confirm API error messages do not expose stack traces in production.

## Reliability review

- Verify transaction rollback on failed multi-record operations.
- Verify duplicate form submissions do not create accidental duplicates.
- Verify missing records produce stable 404 responses.
- Verify invalid state changes produce stable business errors.
- Verify all database migrations apply to an empty database.

## Completion gate

- All critical backend tests pass.
- Frontend type checking and production build pass.
- The MVP happy path passes without manual database repair.
- No known release-blocking security issue remains.

## Suggested commit

```text
test: harden critical workflows for release
```

## Status

```text
IMPLEMENTED AND VERIFIED — 2026-10-05
```

The backend suite now runs only on PostgreSQL. A session fixture rebuilds a dedicated `*_test`
database from the Alembic migrations, and every test runs inside one rolled-back outer
transaction, so results are deterministic and no data leaks between tests. A six-dimension audit
covered secrets, authentication, ownership, input safety, transactions, and the frontend. Its
verified findings were fixed, and each fix is guarded by a test:

- The request session commits or rolls back before the response is sent, using one
  function-scoped dependency shared by routes and authentication.
- Production startup refuses a public or short `SECRET_KEY`, the development `DATABASE_URL`, and
  wildcard or empty `CORS_ORIGINS`. CORS is limited to the methods and headers the SPA uses, with
  no credentials.
- JWTs must carry `exp`, `iat`, `sub`, and `type`.
- Validation errors never echo submitted values.
- NUL text, out-of-range dates, and huge page numbers return 422 instead of 500.
- Quotations and follow-ups under archived leads are hidden everywhere, consistent with the
  dashboard.
- Quotation and follow-up mutations lock their row.
- PDF single-line fields cannot break page layout.
- The demo seed marker is scoped to its owner.
- In the frontend, the query cache is cleared between sessions, and "Save and mark sent" cannot
  create a duplicate after a failed send step.
- The follow-up dialog cannot close mid-save, and lead changes refresh the dashboard.

Evidence:

- 128 backend tests pass on PostgreSQL 17 across repeated runs, and the test database is empty
  afterward.
- The suite covers:
  - a public/protected route inventory checked against OpenAPI;
  - 401 responses on all 20 protected operations;
  - forged and incomplete tokens;
  - indistinguishable login failures;
  - Argon2id parameters;
  - production settings;
  - CORS;
  - hidden 500 internals;
  - a commit failure reported as a 500;
  - malformed IDs;
  - a cross-tenant 404 matrix showing foreign data unchanged;
  - archive rules with dashboard parity;
  - rollback of failed multi-record writes;
  - every illegal transition;
  - duplicate submissions;
  - real two-connection row locks;
  - a migration round trip with no model drift;
  - seed atomicity.
- Reverting each key fix makes its guard test fail.
- Ruff, oxlint, `tsc -b`, the e2e type check, the production build, and `git diff --check` are
  clean.
- All 10 Playwright tests pass, including a new single-run MVP happy path that double-clicks
  every submit and asserts one record per action.

---

# Session 14 — Deployment and Production Verification

## Objective

Deploy the frontend, API, and PostgreSQL database as a provider-independent production system.

## Preparation

- Select hosting providers based on current pricing, PostgreSQL support, deployment reliability, and portfolio-demo needs.
- Keep provider-specific code out of product modules.
- Confirm production environment variables.
- Generate a strong production JWT secret.
- Configure exact production CORS origins.
- Confirm the frontend API URL.
- Confirm HTTPS is used everywhere.

## Database deployment

- Provision managed PostgreSQL.
- Configure secure connection details.
- Apply Alembic migrations.
- Seed the demo user and demo data.
- Confirm the production seed/reset safety guard.

## Backend deployment

- Configure the production start command.
- Configure health checks.
- Configure environment variables.
- Deploy the API.
- Verify API documentation exposure is intentional for the portfolio.
- Confirm production errors do not reveal debugging information.

## Frontend deployment

- Build and deploy the static Vite output.
- Configure SPA route fallback.
- Configure the production API origin.
- Verify browser refresh on nested routes.
- Add appropriate application title, description, and favicon.

## Continuous integration

Add a GitHub Actions workflow that performs the high-value automated checks, such as:

- Backend tests
- Frontend type check
- Frontend production build

Deployment automation may be supplied by the selected hosting platforms.

## Production smoke test

Run the complete MVP flow on the deployed application:

```text
Login
  → Dashboard
  → Create lead
  → Edit lead
  → Create quote
  → Add three items
  → Apply discount and tax
  → Save draft
  → Mark sent
  → Download PDF
  → Add follow-up
  → Complete follow-up
  → Accept quote
  → Confirm lead is won
  → Export CSV
```

## Completion gate

- Public frontend loads over HTTPS.
- Production API is healthy.
- Migrations are current.
- Demo login works.
- The complete MVP flow works in production.
- Direct refresh works on every frontend route.

## Suggested commit

```text
ci: prepare ClientFlow for production deployment
```

## Status

```text
IN PROGRESS — 2026-10-05
```

Repository-side production preparation is implemented and locally verified. The selected portfolio
deployment is a Render Singapore Python API, a Render static frontend, and a Neon Singapore
PostgreSQL database. The checked-in Blueprint configures HTTPS origins, SPA fallback, generated JWT
secret, database-backed health checks, provider-supplied secrets, and deploys only after CI passes.
The API start script applies Alembic migrations and the idempotent demo seed before Uvicorn because
Render's free service does not provide a pre-deploy command.

GitHub Actions now runs Ruff plus the complete backend suite on PostgreSQL 17 and runs frontend lint,
type checking, and the production build. Managed `postgres://` connection strings select psycopg 3
automatically; production CORS requires HTTPS origins; docs/schema exposure is one explicit setting;
and the public demo credential helper reads build-time configuration instead of embedding the local
password. Metadata and the favicon are production-ready.

Local evidence: the official Render schema accepts `render.yaml`; 134 backend tests pass; frontend
lint/build and all 10 Playwright tests pass; and a clean disposable production-mode database reached
the migration head, seeded once, no-op seeded again, authenticated the production demo account, and
returned healthy API/docs/CORS responses. The disposable database was removed afterward.

Still required before this session can be marked complete: create/connect the user's Neon and Render
accounts, enter the three prompted values, deploy from `main`, verify GitHub CI and both public HTTPS
services, run the complete MVP flow against production, test nested-route refreshes, record the live
URLs, commit the final handoff, and push it. Do not start Session 15 before those gates pass.

---

# Session 15 — Portfolio Packaging and Project Handoff

## Objective

Present ClientFlow as a professional engineering case study, not merely a code repository.

## README

Create a complete root README containing:

- Product overview
- Business problem
- Primary workflow
- Feature list
- Screenshots
- Architecture overview
- Technology choices
- Local development setup
- Environment configuration
- Migration and seed instructions
- Test instructions
- Demo credentials or safe demo-login instructions
- Live frontend URL
- API documentation URL when public
- Known v1 limitations
- Possible v2 directions

## Architecture evidence

- Add a clean system architecture diagram.
- Add a simplified entity-relationship diagram.
- Explain ownership authorization.
- Explain why money is calculated using Decimal/NUMERIC.
- Explain the quotation state machine.

## Screenshots

Capture polished images of:

1. Dashboard
2. Lead detail
3. Quotation builder
4. Generated quotation PDF

Use seeded demo data and consistent browser dimensions.

## Demo video

Prepare a 60–90 second demonstration:

```text
Login
  → Dashboard overview
  → Create a lead
  → Create a quotation
  → Show calculations
  → Mark it sent
  → Download PDF
  → Add follow-up
  → Show dashboard update
```

## Case study

Describe:

- The original business problem
- The selected v1 boundary
- The data and authorization design
- The most important implementation challenge
- How quote accuracy is protected
- How the application was tested
- What would be built next for a real client

## Final verification

- Clone or check out the repository into a clean environment.
- Follow the README without undocumented steps.
- Run migrations.
- Seed data.
- Run tests.
- Build the frontend.
- Verify all public links.
- Verify screenshots do not contain private information.
- Tag the finished release as `v1.0.0` when appropriate.

## Completion gate

ClientFlow can be understood, run, reviewed, demonstrated, and evaluated by someone who did not participate in its development.

## Suggested commit

```text
docs: complete ClientFlow portfolio handoff
```

---

## 6. Definition of Done for Every Session

A session is complete only when all applicable statements are true:

- The session objective works through its intended interface.
- Relevant automated tests pass.
- Existing completed workflows still work.
- Database changes include reviewed migrations.
- Ownership rules are tested for new protected resources.
- Loading, empty, error, and success behavior has been considered.
- No real secret was added to source control.
- Environment examples are updated when configuration changes.
- The frontend production build still succeeds after frontend changes.
- Documentation is updated when commands or behavior change.
- The work has a clear commit boundary.

---

## 7. Final MVP Acceptance Checklist

ClientFlow v1 is complete only when all items below work reliably:

- [ ] Demo user can log in.
- [ ] Anonymous users cannot access protected APIs.
- [ ] User A cannot access User B's data.
- [ ] Dashboard displays accurate metrics.
- [ ] Lead can be created.
- [ ] Lead can be searched and filtered.
- [ ] Lead can be edited.
- [ ] Lead can be archived.
- [ ] Lead detail shows its quotations and follow-ups.
- [ ] Quotation requires at least one valid item.
- [ ] Quotation totals are calculated accurately by the backend.
- [ ] Draft quotation can be edited.
- [ ] Sent quotation cannot be freely edited.
- [ ] Quotation can become accepted or rejected through valid transitions.
- [ ] Accepting a quotation marks the lead won.
- [ ] Follow-up can be scheduled.
- [ ] Follow-up appears in the correct timezone-aware group.
- [ ] Follow-up can be completed.
- [ ] Quotation PDF downloads and contains correct totals.
- [ ] Lead CSV downloads safely.
- [ ] Demo data can be reset safely.
- [ ] Primary screens work on mobile and desktop.
- [ ] Keyboard navigation works for primary actions.
- [ ] Backend tests pass.
- [ ] Frontend type checking and production build pass.
- [ ] Clean database can be created entirely with migrations.
- [ ] Production deployment passes the complete smoke test.
- [ ] README and portfolio evidence are complete.

---

## 8. How to Start Each Future Session

At the beginning of a session:

1. Read this document's current session section.
2. Inspect the repository and current Git status.
3. Confirm the previous session's completion gate still passes.
4. Work only within the current session's scope unless a prerequisite defect must be repaired.
5. Verify the session completely before moving its status to complete.

Recommended request format:

```text
Start ClientFlow Session 1 from session.md.
Complete it fully and stop at its completion gate.
```

For later sessions, replace the session number accordingly.


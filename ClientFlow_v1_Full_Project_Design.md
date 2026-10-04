# ClientFlow v1 — Full Project Design

## 1. Product Definition

**Product:** ClientFlow  
**Type:** Full-stack CRM-lite / sales workflow application  
**Target user:** Owner or salesperson at a small service business

### Core Problem

A small business may currently manage prospective clients using:

- Excel / Google Sheets
- WhatsApp / Email
- Manually written quotations
- Calendar reminders

ClientFlow combines the core workflow into one application:

```text
Lead
 ↓
Contact / qualify lead
 ↓
Create quotation
 ↓
Send quotation
 ↓
Schedule follow-up
 ↓
Won / Lost
 ↓
Dashboard + reporting
```

The goal is to build a focused workflow application rather than a large, feature-heavy CRM.

---

## 2. Final v1 Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React + TypeScript |
| Build tooling | Vite |
| Styling | Tailwind CSS |
| Routing | React Router |
| Server state | TanStack Query |
| Forms | React Hook Form |
| Frontend validation | Zod |
| Backend | Python + FastAPI |
| Validation | Pydantic |
| Database | PostgreSQL |
| ORM | SQLAlchemy 2.x |
| Migrations | Alembic |
| Authentication | JWT bearer authentication |
| Password hashing | Argon2 |
| PDF | ReportLab |
| CSV | Python `csv` / backend export |
| Testing | Pytest |
| API docs | FastAPI OpenAPI / Swagger |
| Deployment | Static frontend + deployed FastAPI + managed PostgreSQL |
| Source control | GitHub |

---

## 3. Overall System Architecture

```text
                         INTERNET
                            │
                            ▼
                ┌──────────────────────┐
                │   React Frontend     │
                │                      │
                │ TypeScript           │
                │ Tailwind             │
                │ Forms / Tables       │
                │ Dashboard            │
                └──────────┬───────────┘
                           │
                      HTTPS / JSON
                           │
                           ▼
                ┌──────────────────────┐
                │    FastAPI API       │
                │                      │
                │ Authentication       │
                │ Validation           │
                │ Business Logic       │
                │ Quote Calculations   │
                │ CSV/PDF Generation   │
                └──────────┬───────────┘
                           │
                      SQLAlchemy
                           │
                           ▼
                ┌──────────────────────┐
                │     PostgreSQL       │
                │                      │
                │ Users                │
                │ Leads                │
                │ Quotations           │
                │ Quotation Items      │
                │ Follow-ups           │
                └──────────────────────┘
```

### Architecture Decisions

- No microservices
- No separate authentication server
- No Redis
- No background workers
- No Kubernetes
- One backend application is enough for v1

### Locked Implementation Rules

- Login returns a time-limited JWT access token, stored in browser `sessionStorage`.
- The frontend sends the token as `Authorization: Bearer <token>` and clears it on logout or any `401` response.
- Logout is client-side token removal; the stateless token expires naturally and is not immediately revoked.
- Ownership is enforced inside database queries for leads and every related quotation, follow-up, dashboard aggregate, PDF, and CSV export.
- Persisted money uses PostgreSQL `NUMERIC`; authoritative calculations use Python `Decimal` and are quantized to two decimal places.
- Quotation IDs are UUIDs. A PostgreSQL sequence generates display numbers in the form `Q-2026-00017`; sequence gaps are acceptable.
- Timestamps are stored as timezone-aware UTC values and displayed or categorized in the authenticated user's configured timezone.
- Each user's seeded business profile supplies the business name, address, phone, currency code, and timezone used by the interface and quotation documents.

---

## 4. User Model

For v1, there is only one role:

**User / business owner**

Multiple accounts can exist, but each user only sees their own data.

```text
User A
 └── only sees User A's leads

User B
 └── only sees User B's leads
```

Every lead query must enforce ownership.

Example:

```python
lead.owner_id == current_user.id
```

A demo account will be seeded for portfolio use.

Example:

```text
demo@clientflow.app
********
```

There is no public registration screen in v1.

---

## 5. Complete User Journey

```text
                  ┌─────────┐
                  │  LOGIN  │
                  └────┬────┘
                       │
                       ▼
               ┌───────────────┐
               │   DASHBOARD   │
               └───────┬───────┘
                       │
            ┌──────────┼────────────┐
            ▼          ▼            ▼
          LEADS    FOLLOW-UPS    QUOTATIONS
            │
            ▼
      CREATE LEAD
            │
            ▼
       LEAD DETAILS
       /     │      \
      /      │       \
   EDIT   FOLLOW-UP   QUOTE
            │           │
            │           ▼
            │     QUOTE BUILDER
            │           │
            │           ▼
            │       SAVE DRAFT
            │           │
            │           ▼
            │        SEND
            │           │
            │           ▼
            │      DOWNLOAD PDF
            │
            ▼
      FOLLOW-UP DUE
            │
            ▼
      MARK COMPLETED
            │
            ▼
       WON / LOST
            │
            ▼
        DASHBOARD
```

---

## 6. Navigation Design

Desktop sidebar:

```text
CLIENTFLOW

▣ Dashboard

👥 Leads

📄 Quotations

✓ Follow-ups

──────────────

Mir Abrar
Logout
```

On mobile, this becomes a hamburger/sidebar drawer.

---

# 7. Screen 1 — Login

**URL:**

```text
/login
```

### UI

```text
┌─────────────────────────────────────┐
│                                     │
│             CLIENTFLOW              │
│                                     │
│     Lead & Quotation Management     │
│                                     │
│ Email                               │
│ ┌─────────────────────────────────┐ │
│ │                                 │ │
│ └─────────────────────────────────┘ │
│                                     │
│ Password                            │
│ ┌─────────────────────────────────┐ │
│ │ •••••••••                       │ │
│ └─────────────────────────────────┘ │
│                                     │
│          [ Sign In ]                │
│                                     │
│ Demo credentials available          │
└─────────────────────────────────────┘
```

### Login Flow

```text
Enter credentials
       ↓
POST /auth/login
       ↓
Validate password
       ↓
Generate JWT
       ↓
Frontend stores session token
       ↓
GET /auth/me
       ↓
Dashboard
```

Passwords are never stored as plaintext.

---

# 8. Screen 2 — Dashboard

**URL:**

```text
/dashboard
```

The dashboard should be one of the strongest visual screens because it will likely be used in portfolio screenshots.

### Top Metrics

```text
┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌──────────────┐
│ Total Leads │ │ Open Quotes │ │ Quote Value │ │ Overdue      │
│     42      │ │      8      │ │   $12,450   │ │ Follow-ups 4 │
└─────────────┘ └─────────────┘ └─────────────┘ └──────────────┘
```

### Pipeline

```text
Lead Pipeline

New        Contacted      Qualified      Quoted       Won
 12             8              6             9          7
```

A chart can be added later, but numeric clarity comes first.

### Follow-ups

```text
UPCOMING FOLLOW-UPS

Company          Contact       Date         Status
----------------------------------------------------
Pixel Studio     Sarah         Oct 5        Today
Nexa Ltd         Hasan         Oct 6        Upcoming
Alpha Tech       John          Oct 2        Overdue
```

### Recent Leads

```text
RECENT LEADS

Acme Ltd       John Smith      Qualified
Nova Studio    Sarah Ahmed     New
PixelWorks     Hasan Khan      Quoted
```

### API

```text
GET /api/v1/dashboard/summary
```

Example response:

```json
{
  "total_leads": 42,
  "open_quotes": 8,
  "open_quote_value": 12450,
  "overdue_followups": 4,
  "pipeline": {
    "new": 12,
    "contacted": 8,
    "qualified": 6,
    "quoted": 9,
    "won": 7
  }
}
```

---

# 9. Screen 3 — Leads

**URL:**

```text
/leads
```

## Lead List

```text
LEADS                                         [+ Add Lead]

Search: [________________]

Status: [All ▼]     Source: [All ▼]

┌─────────────────────────────────────────────────────────┐
│ Contact │ Company │ Status │ Value │ Follow-up │ Action│
├─────────────────────────────────────────────────────────┤
│ John    │ Acme    │ New    │ $1200 │ Oct 5     │ View │
│ Sarah   │ Nova    │ Quoted │ $2500 │ Oct 7     │ View │
│ Hasan   │ Pixel   │ Won    │ $1800 │ --        │ View │
└─────────────────────────────────────────────────────────┘

                 < 1 2 3 4 >
```

### Features

- Search
- Status filter
- Source filter
- Pagination
- Create lead
- Open lead
- Archive lead

### Lead Statuses

```text
NEW
CONTACTED
QUALIFIED
QUOTED
WON
LOST
```

Use colored status badges.

---

# 10. Add / Edit Lead

Possible URL:

```text
/leads/new
```

Initially, use a dedicated page rather than a complex modal.

### Fields

| Field | Required |
|---|---:|
| Contact name | Yes |
| Company | No |
| Email | No |
| Phone | No |
| Source | No |
| Estimated value | No |
| Status | Yes |
| Notes | No |

### Lead Sources

```text
Website
Referral
LinkedIn
Upwork
Fiverr
Email
Phone
Other
```

These can remain enum-like values in v1 and do not need a separate table.

---

# 11. Screen 4 — Lead Detail

**URL:**

```text
/leads/:id
```

Example layout:

```text
John Smith
Acme Marketing Ltd.

QUALIFIED

Email: john@acme.com
Phone: +...
Source: Referral
Estimated value: $2,500

[ Edit Lead ] [ Create Quote ] [ Add Follow-up ]

────────────────────────────────

NOTES

Interested in website redesign and API integration.

────────────────────────────────

QUOTATIONS

Q-2026-0015       $1,850       SENT
Q-2026-0011       $1,500       REJECTED

────────────────────────────────

FOLLOW-UPS

Oct 6     Discuss revised proposal       Upcoming
Sep 29    Requirements call              Completed
```

This page acts as the central business record for each lead.

---

# 12. Screen 5 — Quotation Builder

**URL:**

```text
/leads/:leadId/quotes/new
```

Example:

```text
CREATE QUOTATION

Client
Acme Marketing Ltd.

Issue Date
Oct 4, 2026

Valid Until
Oct 18, 2026


ITEMS

Description            Qty      Price       Total

Website design          1       $700        $700

FastAPI backend         1       $500        $500

Deployment              1       $150        $150

                                  [+ Add Item]


Subtotal                             $1,350

Discount       [10] %                -$135

Tax             [5] %                +$60.75

-------------------------------------------

TOTAL                              $1,275.75


Notes
[_______________________________________]


[ Save Draft ]          [ Save & Mark Sent ]
```

## Quotation List

**URL:**

```text
/quotations
```

The list provides search, status filtering, pagination, quote number, client, issue date, total, and status. Selecting a quotation opens its detail page. On narrow screens, rows become stacked cards rather than forcing the primary workflow into horizontal scrolling.

## Quotation Detail

**URL:**

```text
/quotations/:id
```

The detail page shows the quotation header, client, status, issue and validity dates, line items, calculated totals, and notes. It offers only actions valid for the current state: edit a draft, mark a draft sent, accept or reject a sent quotation, and download the PDF.

---

# 13. Quote Calculation Rules

The backend is authoritative.

For every item:

```text
line_total = quantity × unit_price
```

Then:

```text
subtotal = sum(line totals)

discount_amount =
subtotal × discount_percentage / 100

discounted_subtotal =
subtotal - discount_amount

tax_amount =
discounted_subtotal × tax_percentage / 100

total =
discounted_subtotal + tax_amount
```

Example:

```text
Subtotal = $1000

Discount = 10%
         = $100

After discount = $900

Tax = 5%
    = $45

Final total = $945
```

### Money Handling Rule

Do not use normal binary floating point for money.

Use:

- Python `Decimal`
- PostgreSQL `NUMERIC`

---

# 14. Quotation Statuses

```text
DRAFT
   ↓
SENT
   ↓
┌───────────────┐
▼               ▼
ACCEPTED      REJECTED
```

Optional later:

```text
EXPIRED
```

### Rules

**DRAFT**
- Editable

**SENT**
- Not freely editable in v1

**ACCEPTED**
- Automatically changes the lead status to `WON`

**REJECTED**
- Does not automatically change the lead to `LOST`, because another quotation may still be created

---

# 15. Quotation PDF

**Endpoint:**

```text
GET /api/v1/quotations/:id/pdf
```

Example document:

```text
CLIENTFLOW DEMO COMPANY

QUOTATION
Q-2026-00017

Date: October 4, 2026
Valid until: October 18, 2026


BILL TO

Acme Marketing Ltd.
John Smith
john@acme.com


-------------------------------------------------
Description           Qty    Price       Total
-------------------------------------------------
Web Development        1      $700        $700
API Development        1      $500        $500
Deployment             1      $150        $150
-------------------------------------------------

Subtotal                                $1,350
Discount                                 -$135
Tax                                      $60.75

TOTAL                                  $1,275.75
```

This is a major portfolio feature.

---

# 16. Screen 6 — Follow-ups

**URL:**

```text
/follow-ups
```

Sections:

```text
OVERDUE
TODAY
UPCOMING
COMPLETED
```

Example:

```text
OVERDUE

Acme Ltd
Call regarding quotation
Oct 2
[Complete]


TODAY

PixelWorks
Discuss requirements
Oct 4
[Complete]


UPCOMING

Nova Agency
Proposal review
Oct 7
```

Clicking the company should open the lead detail page.

---

# 17. Follow-up Workflow

```text
Lead page
   ↓
Add Follow-up
   ↓
Date/time + note
   ↓
Saved
   ↓
Shows on Dashboard
   ↓
Date passes
   ↓
Becomes Overdue
   ↓
User clicks Complete
   ↓
completed_at recorded
```

No email/SMS notification service in v1.

---

# 18. CSV Export

Button:

```text
Export Leads
```

**Endpoint:**

```text
GET /api/v1/leads/export
```

Example output:

```csv
Contact Name,Company,Email,Phone,Status,Source,Estimated Value,Created At
John Smith,Acme Ltd,john@acme.com,...,Qualified,Referral,2500,...
```

This demonstrates a practical business automation feature.

---

# 19. Database Design

```text
             USER
              │
              │ 1
              │
              │ N
             LEAD
           /      \
          /        \
         N          N
 QUOTATION       FOLLOW_UP
      │
      │ 1
      │
      │ N
QUOTATION_ITEM
```

## `users`

```text
id
email
full_name
password_hash
is_active
business_name
business_address
business_phone
currency_code
timezone
created_at
updated_at
```

## `leads`

```text
id
owner_id → users.id

contact_name
company
email
phone
source

status
estimated_value

notes

is_archived

created_at
updated_at
```

## `quotations`

```text
id
lead_id → leads.id

quote_number

status

issue_date
valid_until

subtotal
discount_percent
discount_amount

tax_percent
tax_amount

total

notes

created_at
updated_at
```

## `quotation_items`

```text
id
quotation_id → quotations.id

description
quantity
unit_price
line_total

sort_order
```

## `follow_ups`

```text
id
lead_id → leads.id

due_at
note

is_completed
completed_at

created_at
updated_at
```

Only five core tables are required in v1.

---

# 20. IDs

Use UUIDs.

Example:

```text
9f7d8e39-a455-4ce8-b748-22f0cbfe5431
```

rather than sequential public IDs such as:

```text
17
```

---

# 21. API Architecture

All API endpoints use:

```text
/api/v1/...
```

This leaves room for a future:

```text
/api/v2/
```

without breaking v1 clients.

---

# 22. Authentication API

```text
POST /api/v1/auth/login

GET  /api/v1/auth/me

POST /api/v1/auth/logout
```

No public `/register` endpoint in v1.

---

# 23. Lead API

```text
GET    /api/v1/leads
POST   /api/v1/leads

GET    /api/v1/leads/{id}
PATCH  /api/v1/leads/{id}

POST   /api/v1/leads/{id}/archive

GET    /api/v1/leads/export
```

### Filters

```text
?page=1
&page_size=20
&status=QUALIFIED
&source=Referral
&search=acme
```

Example response:

```json
{
  "items": [],
  "page": 1,
  "page_size": 20,
  "total": 42,
  "pages": 3
}
```

---

# 24. Quotation API

```text
POST /api/v1/leads/{lead_id}/quotations

GET /api/v1/leads/{lead_id}/quotations

GET /api/v1/quotations

GET /api/v1/quotations/{id}

PATCH /api/v1/quotations/{id}

PATCH /api/v1/quotations/{id}/status

GET /api/v1/quotations/{id}/pdf
```

The top-level quotation list supports pagination, status filtering, and client or quote-number search.

Example request:

```json
{
  "valid_until": "2026-10-18",
  "discount_percent": 10,
  "tax_percent": 5,
  "items": [
    {
      "description": "Website Development",
      "quantity": 1,
      "unit_price": "700.00"
    },
    {
      "description": "API Integration",
      "quantity": 2,
      "unit_price": "100.00"
    }
  ]
}
```

The client does not send trusted totals. The backend recalculates all monetary values.

---

# 25. Follow-up API

```text
POST  /api/v1/leads/{id}/follow-ups

GET   /api/v1/follow-ups

PATCH /api/v1/follow-ups/{id}

PATCH /api/v1/follow-ups/{id}/complete
```

### Filters

```text
?status=overdue

?status=today

?status=upcoming

?status=completed
```

---

# 26. Dashboard API

```text
GET /api/v1/dashboard/summary
```

One request should provide all major dashboard statistics.

---

# 27. Backend Architecture

Repository:

```text
clientflow/
│
├── backend/
│
├── frontend/
│
├── README.md
├── .gitignore
└── docker-compose.yml
```

Backend structure:

```text
backend/
│
├── app/
│   │
│   ├── main.py
│   │
│   ├── api/
│   │   └── v1/
│   │       ├── auth.py
│   │       ├── leads.py
│   │       ├── quotations.py
│   │       ├── followups.py
│   │       └── dashboard.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   └── security.py
│   │
│   ├── db/
│   │   ├── base.py
│   │   └── session.py
│   │
│   ├── models/
│   │   ├── user.py
│   │   ├── lead.py
│   │   ├── quotation.py
│   │   └── followup.py
│   │
│   ├── schemas/
│   │   ├── auth.py
│   │   ├── lead.py
│   │   ├── quotation.py
│   │   └── followup.py
│   │
│   ├── services/
│   │   ├── quotation_service.py
│   │   ├── dashboard_service.py
│   │   ├── pdf_service.py
│   │   └── export_service.py
│   │
│   └── dependencies/
│       ├── auth.py
│       └── database.py
│
├── tests/
│
├── alembic/
├── alembic.ini
├── pyproject.toml
└── .env.example
```

### Separation of Responsibilities

```text
router
   ↓
service / business logic
   ↓
SQLAlchemy
   ↓
database
```

Business logic should not be dumped directly into route files.

---

# 28. Frontend Architecture

```text
frontend/
│
├── src/
│   │
│   ├── app/
│   │   ├── App.tsx
│   │   ├── router.tsx
│   │   └── queryClient.ts
│   │
│   ├── components/
│   │   ├── layout/
│   │   └── ui/
│   │
│   ├── features/
│   │   ├── auth/
│   │   ├── dashboard/
│   │   ├── leads/
│   │   ├── quotations/
│   │   └── followups/
│   │
│   ├── lib/
│   │   ├── apiClient.ts
│   │   ├── errors.ts
│   │   └── formatting.ts
│   │
│   ├── types/
│   ├── index.css
│   └── main.tsx
│
└── .env.example
```

---

# 29. Validation Rules

## Lead

```text
contact_name:
1–100 characters

email:
valid email if supplied

estimated_value:
>= 0

notes:
reasonable maximum length
```

## Quote

```text
At least 1 item

quantity > 0

unit_price >= 0

discount:
0–100%

tax:
0–100%

valid_until >= issue_date

description cannot be blank
```

## Follow-up

```text
note required

due_at required
```

---

# 30. Authorization Rule

A logged-in user must never be able to access another user's resource.

Example that must be blocked:

```text
GET /leads/<another-user-lead-id>
```

Ownership checks must apply to:

- Leads
- Quotations
- Follow-ups
- Dashboard aggregates
- CSV exports
- PDF exports

---

# 31. Error Design

Poor error:

```json
{
  "detail": "Something went wrong"
}
```

Better:

```json
{
  "detail": {
    "code": "QUOTE_NOT_EDITABLE",
    "message": "Only draft quotations can be edited."
  }
}
```

The frontend then shows the human-readable message.

---

# 32. UI States

Every major screen should handle:

```text
Loading

Empty

Success

Error
```

Example empty state:

```text
No leads yet.

Add your first lead to start tracking
your sales pipeline.

[ Add Lead ]
```

Avoid blank tables with no explanation.

---

# 33. Demo Seed Data

The project will ship with fictional business data.

Suggested volume:

```text
1 demo user

25–40 leads

8 quotations

15 quotation items

12 follow-ups
```

Use multiple statuses:

```text
NEW
CONTACTED
QUALIFIED
QUOTED
WON
LOST
```

This ensures portfolio screenshots look realistic.

---

# 34. Testing Strategy

We do not need hundreds of tests. Focus on critical business behavior.

## Authentication

```text
✓ correct password logs in

✓ wrong password rejected

✓ protected endpoint rejects anonymous request
```

## Authorization

```text
✓ User A can access own lead

✓ User A cannot access User B's lead
```

## Leads

```text
✓ create

✓ update

✓ search/filter

✓ archive
```

## Quotations

```text
✓ subtotal calculation

✓ discount calculation

✓ tax calculation

✓ total calculation

✓ invalid negative quantity rejected

✓ quote requires at least one item

✓ SENT quote cannot be edited
```

## Follow-ups

```text
✓ upcoming detected

✓ overdue detected

✓ completion recorded
```

---

# 35. Git Strategy

Main branch:

```text
main
```

Feature branches:

```text
feature/project-setup

feature/auth

feature/leads

feature/quotations

feature/followups

feature/dashboard

feature/pdf-export

feature/ui-polish
```

Example commits:

```text
feat: add lead SQLAlchemy model

feat: implement paginated lead API

feat: add quotation calculation service

test: verify quotation tax calculation

feat: add overdue follow-up query

fix: prevent cross-user lead access
```

Avoid vague commit names such as:

```text
update
update2
final
final-final
working-final
```

---

# 36. Environment Configuration

Backend:

```text
DATABASE_URL=
SECRET_KEY=
ACCESS_TOKEN_EXPIRE_MINUTES=
CORS_ORIGINS=
ENVIRONMENT=
```

Frontend:

```text
VITE_API_URL=
```

Commit:

```text
.env.example
```

Never commit real secrets from:

```text
.env
```

---

# 37. Database Migrations

Workflow:

```text
Modify SQLAlchemy model
        ↓
Generate Alembic migration
        ↓
Review migration
        ↓
Run migration
        ↓
Database updated
```

Database changes should always be version-controlled.

---

# 38. Deployment Architecture

```text
                    Internet
                       │
          ┌────────────┴────────────┐
          ▼                         ▼
   React Frontend              FastAPI
   Static Hosting                API
                                   │
                                   ▼
                              PostgreSQL
```

The code should not depend on one hosting provider.

It should only require standard environment configuration.

---

# 39. Portfolio Evidence

When the project is finished, collect:

## Screenshot 1
Dashboard

## Screenshot 2
Lead detail page

## Screenshot 3
Quotation builder

## Screenshot 4
Generated PDF quotation

## Demo Video

Target: 60–90 seconds.

```text
Login
 ↓
Dashboard
 ↓
Create lead
 ↓
Create quotation
 ↓
Add line items
 ↓
See calculation
 ↓
Mark sent
 ↓
Download PDF
 ↓
Add follow-up
 ↓
Dashboard updates
```

## GitHub
Professional README

## Live Demo
Public URL

---

# 40. Explicitly Out of v1 Scope

Do not build these in v1:

| Feature | Decision |
|---|---|
| AI assistant | ❌ |
| Chat | ❌ |
| Stripe | ❌ |
| Subscription billing | ❌ |
| WhatsApp integration | ❌ |
| Email sending | ❌ |
| Google OAuth | ❌ |
| Multi-company tenancy | ❌ |
| Staff roles | ❌ |
| Complex permissions | ❌ |
| Inventory | ❌ |
| Accounting | ❌ |
| Mobile app | ❌ |
| Real-time sockets | ❌ |
| Calendar sync | ❌ |
| Marketing automation | ❌ |

These can become v2 features later if needed.

---

# 41. Exact Development Sequence

## Phase 0 — Foundation

```text
Create GitHub repository
↓
Create backend/
↓
Create frontend/
↓
Create Python environment
↓
Install FastAPI
↓
Create React/Vite project
↓
Configure environment variables
↓
Create PostgreSQL development database
↓
Verify frontend ↔ backend connection
```

### Milestone

```text
React page loads
        +
GET /api/v1/health → 200
```

---

## Phase 1 — Database Foundation

Build:

```text
User
Lead
Quotation
QuotationItem
FollowUp
```

Then:

```text
Alembic
↓
initial migration
↓
PostgreSQL tables
```

### Milestone

Database structure exists cleanly.

---

## Phase 2 — Authentication

Build:

```text
password hashing
↓
demo user
↓
login endpoint
↓
JWT
↓
current-user dependency
↓
protected API
↓
React login
↓
protected frontend routes
```

### Milestone

```text
Login
 ↓
Dashboard placeholder
```

---

## Phase 3 — Leads

Backend first:

```text
POST lead
GET leads
GET lead
PATCH lead
archive lead
search
filter
pagination
```

Then frontend:

```text
Lead list
Lead form
Lead detail
```

### Milestone

```text
Login
 ↓
Create lead
 ↓
See it in list
 ↓
Edit it
 ↓
Open details
```

This is the first complete vertical slice.

---

## Phase 4 — Quotations

Build:

```text
Quotation model logic
↓
Quotation items
↓
Decimal calculations
↓
Create API
↓
Update draft API
↓
Status changes
↓
React quote builder
```

### Milestone

```text
Lead
 ↓
Create Quote
 ↓
Add items
 ↓
Correct total
 ↓
Save
```

---

## Phase 5 — Follow-ups

Build:

```text
Create follow-up
↓
Upcoming query
↓
Overdue query
↓
Complete follow-up
↓
Follow-up UI
```

### Milestone

Full lead-management workflow works.

---

## Phase 6 — Dashboard

Aggregate:

```text
lead counts
quote counts
open quote value
pipeline counts
overdue follow-ups
recent leads
```

Then build dashboard UI.

---

## Phase 7 — CSV + PDF

Build:

```text
CSV lead export

PDF quotation generation
```

At this point, ClientFlow becomes a strong portfolio demo.

---

## Phase 8 — Testing

Critical test areas:

```text
Authentication
Authorization
Lead CRUD
Quote mathematics
Follow-up logic
```

---

## Phase 9 — Polish

Add:

```text
Loading states
Empty states
Error messages
Responsive layout
Toast notifications
Confirmation dialogs
404 page
```

---

## Phase 10 — Deployment

```text
PostgreSQL
↓
Backend
↓
Frontend
↓
Run migrations
↓
Seed demo database
↓
Test public application
```

---

## Phase 11 — Portfolio Packaging

```text
README
Screenshots
Architecture diagram
Demo video
Live URL
GitHub pin
Portfolio case study
Fiverr images
Upwork portfolio item
```

---

# 42. MVP Completion Test

ClientFlow is complete when this full flow works reliably:

```text
Login as demo user
       ↓
View dashboard
       ↓
Create Acme Ltd lead
       ↓
Set status = Qualified
       ↓
Create quotation
       ↓
Add 3 line items
       ↓
Apply discount + tax
       ↓
Verify total
       ↓
Save quotation
       ↓
Mark it Sent
       ↓
Generate PDF
       ↓
Schedule follow-up
       ↓
See follow-up on dashboard
       ↓
Mark follow-up complete
       ↓
Mark quotation Accepted
       ↓
Lead automatically becomes Won
       ↓
Export leads to CSV
```

If all of this works reliably, Project A is complete.

---

# 43. Final Architecture Summary

```text
                    CLIENTFLOW v1

                       LOGIN
                         │
                         ▼
                     DASHBOARD
                         │
          ┌──────────────┼──────────────┐
          │              │              │
          ▼              ▼              ▼
        LEADS       QUOTATIONS      FOLLOW-UPS
          │              │              │
          ▼              ▼              ▼
      Lead Detail   Quote Builder    Due Tasks
          │              │
          └───────┬──────┘
                  │
                  ▼
              PDF / CSV
```

Technology flow:

```text
React + TypeScript + Tailwind
             ↓
         FastAPI
             ↓
       SQLAlchemy
             ↓
        PostgreSQL
```

---

# 44. First Build Target

Do not start with dashboard visuals.

Start with:

```text
Repository
↓
FastAPI skeleton
↓
PostgreSQL
↓
SQLAlchemy
↓
Alembic
↓
User + Lead models
↓
Authentication
↓
First Lead API
```

Then connect React.

This keeps the frontend from being built on top of an unstable backend.

---

# 45. Project Success Criteria

ClientFlow v1 should prove that the developer can:

- Translate a real business workflow into software
- Build a production-style Python REST API
- Design relational database models
- Implement authentication and ownership-based authorization
- Build a modern React frontend
- Handle form validation and user-facing errors
- Implement accurate money calculations
- Generate PDFs and CSV exports
- Write important automated tests
- Run database migrations
- Deploy a full-stack application
- Document and present the project professionally

The project should feel like a small real client system, not a classroom CRUD demo.

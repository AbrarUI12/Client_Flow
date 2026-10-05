# ClientFlow production deployment

The checked-in production recipe uses Render for the HTTPS API and static frontend, plus Supabase for
managed PostgreSQL. Application code remains provider-independent: the API only consumes standard
environment variables and a PostgreSQL connection URL.

## Why these providers

- Render provides a free static CDN, managed TLS, GitHub deploys, SPA rewrites, and a free Python
  web service. The free API sleeps after 15 idle minutes, so the first request can take about a
  minute. This is acceptable for a portfolio demo, not an always-on business workload.
- Render's free PostgreSQL expires after 30 days. Supabase is used instead because its free database
  has no fixed 30-day expiry and is available in Asia Pacific. A low-activity free
  project can pause after seven days and must then be restored from the Supabase dashboard.

Provider limits and pricing can change. Recheck them before recreating the deployment.

Current provider references (checked 2026-10-06):

- [Render free-service limits](https://render.com/docs/free)
- [Render Blueprint specification](https://render.com/docs/blueprint-spec)
- [Supabase pricing](https://supabase.com/pricing)
- [Supabase free-project pausing](https://supabase.com/docs/guides/platform/free-project-pausing)
- [Supabase database connections](https://supabase.com/docs/guides/database/connecting-to-postgres)
- [Supabase regions](https://supabase.com/docs/guides/platform/regions)

## 1. Create PostgreSQL on Supabase

1. Create a Supabase project named `clientflow`. The current production project uses Tokyo
   (`ap-northeast-1`); save its database password in a password manager.
2. In the project's **Connect** dialog, select **Session pooler** and copy the port `5432`
   connection string. Render needs this IPv4-compatible pooler; do not use the direct connection,
   which requires IPv6, or the port `6543` transaction pooler.
3. Replace the password placeholder and append `?sslmode=require` if the copied URL has no query
   string. A normal `postgresql://...` or `postgres://...` URL is accepted; ClientFlow selects
   psycopg automatically.
4. Do not commit or paste the URL into chat. Enter it only as Render's secret `DATABASE_URL`.

The production start script runs `alembic upgrade head` before the API process, then runs the
idempotent demo seed. A failed migration or seed prevents the new process from reporting healthy.

## 2. Create the Render Blueprint

1. In Render, create a new Blueprint from `AbrarUI12/Client_Flow` on `main`.
2. Render reads the root `render.yaml`. For this deployment, Render assigned the globally unique
   service names `clientflow-api-abrarui12-kocw` and `clientflow-web-abrarui12-kocw`.
3. When prompted, set `DATABASE_URL` to the Supabase Session Pooler connection string.
4. Choose one public demo password of at least 16 characters and enter the exact same value for
   both `DEMO_USER_PASSWORD` and `VITE_DEMO_PASSWORD`.

`VITE_DEMO_PASSWORD` is bundled into the public JavaScript intentionally so visitors can use the
demo account; it must not be reused for anything private. Render generates the private JWT signing
key and never exposes it to the frontend.

The API start command is `bash scripts/start-production.sh`. Render's free plan does not offer a
separate pre-deploy command, so the idempotent migration and seed run at process start. The health
check calls `/api/v1/health`, which also proves PostgreSQL is reachable. Interactive API docs are
intentionally enabled at `/docs` for the portfolio deployment; setting `EXPOSE_API_DOCS=false`
hides both `/docs` and `/openapi.json` in production.

## 3. Verify the deployment

Production verification completed successfully on 2026-10-06. The URLs below are live, and the
documented production smoke command passed all three public browser tests.

Expected URLs:

```text
Frontend: https://clientflow-web-abrarui12-kocw.onrender.com
API:      https://clientflow-api-abrarui12-kocw.onrender.com
Health:   https://clientflow-api-abrarui12-kocw.onrender.com/api/v1/health
Docs:     https://clientflow-api-abrarui12-kocw.onrender.com/docs
```

Verify that the health response is 200, the current Alembic revision is the migration head in the
deploy log, and a direct browser refresh works on `/dashboard`, `/leads`, `/quotations`, and
`/follow-ups`. Then run the complete Session 14 MVP smoke flow from `session.md` and record the
public URLs and result in `AGENTS.md`.

From `frontend`, the production smoke command targets the public services explicitly. It runs the
complete MVP flow plus the nested-route refresh, 404, responsive-layout, and accessibility checks
serially. The longer timeout allows for a free API cold start:

```powershell
$env:PLAYWRIGHT_BASE_URL='https://clientflow-web-abrarui12-kocw.onrender.com'
$env:VITE_API_URL='https://clientflow-api-abrarui12-kocw.onrender.com/api/v1'
npm run test:smoke:production
Remove-Item Env:PLAYWRIGHT_BASE_URL, Env:VITE_API_URL
```

## Production environment contract

Required API variables:

```text
ENVIRONMENT=production
DATABASE_URL=<secret managed PostgreSQL URL>
SECRET_KEY=<generated private value of at least 32 bytes>
CORS_ORIGINS=https://clientflow-web-abrarui12-kocw.onrender.com
DEMO_USER_PASSWORD=<public demo-only password, not the development default>
```

Required frontend build variables:

```text
VITE_API_URL=https://clientflow-api-abrarui12-kocw.onrender.com/api/v1
VITE_DEMO_EMAIL=demo@clientflow.app
VITE_DEMO_PASSWORD=<same public demo-only password>
```

ClientFlow refuses unsafe production configuration at startup. The reset command is disabled in
production; the normal seed is idempotent and affects only the configured demo account.

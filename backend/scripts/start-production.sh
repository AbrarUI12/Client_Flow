#!/usr/bin/env bash
set -euo pipefail

# Free hosting plans do not provide a separate release phase. Both operations are idempotent, so
# running them before every process start safely handles deploys and cold starts.
python -m alembic upgrade head
python -m app.scripts.seed_demo_user
exec python -m uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" --proxy-headers

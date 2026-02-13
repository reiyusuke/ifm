#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
source .venv/bin/activate

lsof -ti :8000 2>/dev/null | xargs kill -9 2>/dev/null || true

exec python -m uvicorn app.main:app \
  --host 127.0.0.1 \
  --port 8000 \
  --reload \
  --log-level debug \
  --env-file .env

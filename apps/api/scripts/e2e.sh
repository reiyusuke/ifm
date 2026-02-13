#!/usr/bin/env bash
set -euxo pipefail

cd "$(dirname "$0")/.."
source .venv/bin/activate

LOG_FILE="${LOG_FILE:-/tmp/uvicorn_e2e.log}"
API_HOST="${API_HOST:-127.0.0.1}"
API_PORT="${API_PORT:-8000}"

echo "=== kill existing :8000 listeners ==="
PIDS=($(lsof -tiTCP:${API_PORT} -sTCP:LISTEN || true))
for PID in "${PIDS[@]:-}"; do
  kill -TERM "$PID" || true
done
sleep 0.3
PIDS=($(lsof -tiTCP:${API_PORT} -sTCP:LISTEN || true))
for PID in "${PIDS[@]:-}"; do
  kill -KILL "$PID" || true
done

echo "=== reset test DB ==="
rm -f app_test.db

export API_BASE_URL="http://${API_HOST}:${API_PORT}"
export E2E_DB_PATH="app_test.db"
export DATABASE_URL="sqlite:///./app_test.db"

echo "=== init schema & seed users in app_test.db ==="
python scripts/seed_e2e_db.py

echo "=== start server (DATABASE_URL=${DATABASE_URL}) ==="
UVICORN_ARGS=(app.main:app --host "${API_HOST}" --port "${API_PORT}")

# .env が存在する時だけ読み込む（CIで落ちないようにする）
if [[ -f ".env" ]]; then
  UVICORN_ARGS+=(--env-file .env)
fi

python -m uvicorn "${UVICORN_ARGS[@]}" > "${LOG_FILE}" 2>&1 &
UVICORN_PID=$!
echo "UVICORN_PID=${UVICORN_PID}"

echo "=== wait health ==="
for i in {1..100}; do
  if curl -sS "${API_BASE_URL}/health" >/dev/null 2>&1; then
    break
  fi
  sleep 0.1
done

echo "=== run tests ==="
pytest -vv -s | tee pytest.log || EXIT_CODE=$?

if [[ "${EXIT_CODE:-0}" -ne 0 ]]; then
  echo "=== pytest failed (exit=${EXIT_CODE}) ==="
  echo "---- ${LOG_FILE} (tail) ----"
  tail -n 200 "${LOG_FILE}" || true
fi

echo "=== stop server ==="
kill -TERM "${UVICORN_PID}" 2>/dev/null || true
sleep 0.2
kill -KILL "${UVICORN_PID}" 2>/dev/null || true

exit "${EXIT_CODE:-0}"

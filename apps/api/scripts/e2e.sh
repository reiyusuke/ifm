#!/usr/bin/env bash
set -euxo pipefail

cd "$(dirname "$0")/.."

# shellcheck disable=SC1091
source .venv/bin/activate

LOG_FILE=/tmp/uvicorn_e2e.log
API_HOST="${API_HOST:-127.0.0.1}"
API_PORT="${API_PORT:-8000}"

echo "=== kill existing :${API_PORT} listeners ==="
PIDS="$(lsof -tiTCP:${API_PORT} -sTCP:LISTEN 2>/dev/null || true)"
if [[ -n "${PIDS}" ]]; then
  for pid in ${PIDS}; do
    kill -TERM "${pid}" 2>/dev/null || true
  done
fi
sleep 0.3
PIDS="$(lsof -tiTCP:${API_PORT} -sTCP:LISTEN 2>/dev/null || true)"
if [[ -n "${PIDS}" ]]; then
  for pid in ${PIDS}; do
    kill -KILL "${pid}" 2>/dev/null || true
  done
fi

echo "=== reset test DB ==="
rm -f app_test.db

export API_BASE_URL="http://${API_HOST}:${API_PORT}"
export E2E_DB_PATH="app_test.db"
export DATABASE_URL="sqlite:///./app_test.db"

echo "=== init schema & seed users in app_test.db ==="
python scripts/seed_e2e_db.py

echo "=== start server (DATABASE_URL=${DATABASE_URL}) ==="
ENV_ARGS=()
if [[ -f .env ]]; then
  ENV_ARGS+=(--env-file .env)
fi

python -m uvicorn app.main:app --host "${API_HOST}" --port "${API_PORT}" "${ENV_ARGS[@]}" > "${LOG_FILE}" 2>&1 &
UVICORN_PID=$!
echo "UVICORN_PID=${UVICORN_PID}"

echo "=== wait health ==="
READY=0
for _ in $(seq 1 100); do
  if curl -sS "${API_BASE_URL}/health" >/dev/null 2>&1; then
    READY=1
    break
  fi
  sleep 0.1
done

if [[ "${READY}" -ne 1 ]]; then
  echo "Health check failed"
  echo "---- ${LOG_FILE} (tail) ----"
  tail -n 200 "${LOG_FILE}" || true
  kill -TERM "${UVICORN_PID}" 2>/dev/null || true
  sleep 0.2
  kill -KILL "${UVICORN_PID}" 2>/dev/null || true
  exit 1
fi

EXIT_CODE=0
echo "=== run tests ==="
pytest -vv -s | tee pytest.log || EXIT_CODE=$?

if [[ "${EXIT_CODE}" -ne 0 ]]; then
  echo "=== pytest failed (exit=${EXIT_CODE}) ==="
  echo "---- ${LOG_FILE} (tail) ----"
  tail -n 200 "${LOG_FILE}" || true
fi

echo "=== stop server ==="
kill -TERM "${UVICORN_PID}" 2>/dev/null || true
sleep 0.2
kill -KILL "${UVICORN_PID}" 2>/dev/null || true

exit "${EXIT_CODE}"

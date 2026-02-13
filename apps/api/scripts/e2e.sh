#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
source .venv/bin/activate

API_HOST="127.0.0.1"
API_PORT="8000"
API="http://${API_HOST}:${API_PORT}"
LOG_FILE="/tmp/uvicorn_e2e.log"

echo "=== kill existing :8000 listeners ==="
PIDS="$(lsof -tiTCP:${API_PORT} -sTCP:LISTEN 2>/dev/null || true)"
if [[ -n "${PIDS}" ]]; then
  for PID in ${PIDS}; do
    kill -TERM "${PID}" 2>/dev/null || true
  done
  sleep 0.3
  PIDS2="$(lsof -tiTCP:${API_PORT} -sTCP:LISTEN 2>/dev/null || true)"
  if [[ -n "${PIDS2}" ]]; then
    for PID in ${PIDS2}; do
      kill -KILL "${PID}" 2>/dev/null || true
    done
  fi
fi

echo "=== reset test DB ==="
rm -f app_test.db

export API_BASE_URL="${API}"
export E2E_DB_PATH="app_test.db"
export DATABASE_URL="sqlite:///./app_test.db"

echo "=== init schema & seed users in app_test.db ==="
python - <<'PY'
import inspect
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import engine
from app.models.models import Base, User, UserRole
import app.models.models  # noqa: F401 (register models)

import app.security as sec

Base.metadata.create_all(bind=engine)

# auth.py は app.security.verify_password を使うので、
# それと対になる "hash" を app.security から自動で探して使う
CANDIDATES = [
    "get_password_hash",
    "hash_password",
    "create_password_hash",
    "password_hash",
    "hash",
    "make_password_hash",
]

hash_fn = None
for name in CANDIDATES:
    fn = getattr(sec, name, None)
    if callable(fn):
        hash_fn = fn
        break

if hash_fn is None:
    # 1引数の callable を拾う（最後の保険）
    for name, fn in sec.__dict__.items():
        if not callable(fn) or name.startswith("_"):
            continue
        try:
            sig = inspect.signature(fn)
        except Exception:
            continue
        if len(sig.parameters) == 1:
            hash_fn = fn
            break

if hash_fn is None:
    raise SystemExit("ERROR: password hash function not found in app.security")

print("USING_HASH_FN =", hash_fn.__name__)

BUYER_EMAIL="realbuyer@ifm.com"
BUYER_PASS="buyerpass"
SELLER_EMAIL="seller@ifm.com"
SELLER_PASS="sellerpass"

def ensure_user(db: Session, email: str, pw: str, role):
    email_norm = email.strip().lower()
    u = db.execute(select(User).where(User.email == email_norm)).scalar_one_or_none()
    if u:
        return
    db.add(User(
        email=email_norm,
        password_hash=hash_fn(pw),
        role=role,
        status="ACTIVE",
    ))
    db.commit()

with Session(engine) as db:
    ensure_user(db, BUYER_EMAIL, BUYER_PASS, UserRole.BUYER.value if hasattr(UserRole.BUYER, "value") else UserRole.BUYER)
    ensure_user(db, SELLER_EMAIL, SELLER_PASS, UserRole.SELLER.value if hasattr(UserRole.SELLER, "value") else UserRole.SELLER)

print("OK: schema created & users seeded")
PY

echo "=== start server (DATABASE_URL=${DATABASE_URL}) ==="
: > "${LOG_FILE}"
python -m uvicorn app.main:app --host "${API_HOST}" --port "${API_PORT}" --env-file .env >"${LOG_FILE}" 2>&1 &
UVICORN_PID=$!
echo "UVICORN_PID=${UVICORN_PID}"

echo "=== wait health ==="
for i in {1..200}; do
  if curl -sS "${API}/health" >/dev/null 2>&1; then
    break
  fi
  sleep 0.05
done

echo "=== run tests ==="
set +e
pytest -vv -s | tee pytest.log
EXIT_CODE=$?
set -e

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

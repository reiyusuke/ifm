#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
from pathlib import Path

from sqlalchemy import select, create_engine
from sqlalchemy.orm import Session

# --- ensure "import app" works no matter where it is executed ---
API_ROOT = Path(__file__).resolve().parents[1]  # apps/api
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

# --- import Base & models so metadata includes all tables ---
from app.db.base import Base  # noqa: E402
import app.models.models  # noqa: F401,E402  (important: register models)
from app.models.models import User  # noqa: E402
from app.models.enums import UserRole  # noqa: E402

# --- password hash function: use the same function as the app uses for verification ---
HASH_FN = None
HASH_FN_NAME = "unknown"
try:
    from app.security import get_password_hash as _h  # type: ignore  # noqa: E402

    HASH_FN = _h
    HASH_FN_NAME = "get_password_hash(app.security)"
except Exception:
    try:
        from app.auth.security import get_password_hash as _h2  # type: ignore  # noqa: E402

        HASH_FN = _h2
        HASH_FN_NAME = "get_password_hash(app.auth.security)"
    except Exception as e:
        raise RuntimeError(f"Cannot import get_password_hash: {e}") from e


BUYER_EMAIL = os.getenv("E2E_BUYER_EMAIL", "realbuyer@ifm.com").strip().lower()
BUYER_PASS = os.getenv("E2E_BUYER_PASS", "buyerpass")
SELLER_EMAIL = os.getenv("E2E_SELLER_EMAIL", "realseller@ifm.com").strip().lower()
SELLER_PASS = os.getenv("E2E_SELLER_PASS", "sellerpass")

DB_URL = os.getenv("DATABASE_URL", "sqlite:///./app_test.db")


def ensure_user(db: Session, email: str, plain_password: str, role_value: str) -> None:
    email = email.strip().lower()
    u = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if u:
        return

    pw_hash = HASH_FN(plain_password)
    db.add(
        User(
            email=email,
            password_hash=pw_hash,
            role=role_value,
            status="ACTIVE",
        )
    )
    db.commit()


def main() -> None:
    # Create engine FROM DATABASE_URL explicitly (prevents "seeded different DB" issues)
    engine = create_engine(DB_URL, future=True)

    # Create schema
    Base.metadata.create_all(bind=engine)

    # Seed users
    with Session(engine) as db:
        ensure_user(db, BUYER_EMAIL, BUYER_PASS, UserRole.BUYER.value)
        ensure_user(db, SELLER_EMAIL, SELLER_PASS, UserRole.SELLER.value)

        buyer = db.execute(select(User).where(User.email == BUYER_EMAIL)).scalar_one_or_none()
        seller = db.execute(select(User).where(User.email == SELLER_EMAIL)).scalar_one_or_none()
        print(f"USING_HASH_FN = {HASH_FN_NAME}")
        print(f"DB_URL = {DB_URL}")
        print(f"SEEDED buyer={bool(buyer)} seller={bool(seller)}")

    print("OK: schema created & users seeded")


if __name__ == "__main__":
    main()

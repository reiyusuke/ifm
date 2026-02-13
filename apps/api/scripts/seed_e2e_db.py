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


# --- IMPORTANT ---
# Use the SAME Base / User model module that the app uses.
# app/routers/auth.py imports User from app.models.models
import app.models.models as models  # noqa: E402

User = models.User  # type: ignore[attr-defined]
Base = getattr(models, "Base", None)

if Base is None:
    # fallback: if your project defines Base in app.db.base
    from app.db.base import Base  # type: ignore  # noqa: E402


# role enum (project-specific)
try:
    from app.models.enums import UserRole  # type: ignore  # noqa: E402
except Exception:
    class UserRole:  # type: ignore
        BUYER = "BUYER"
        SELLER = "SELLER"


# password hash function (must match verify_password path)
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


def ensure_user(db: Session, email: str, password: str, role_value: str) -> None:
    u = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if u:
        u.role = role_value
        u.status = getattr(u, "status", None) or "ACTIVE"
        if not getattr(u, "password_hash", None):
            u.password_hash = HASH_FN(password)  # type: ignore[misc]
        db.commit()
        return

    db.add(
        User(
            email=email,
            password_hash=HASH_FN(password),  # type: ignore[misc]
            role=role_value,
            status="ACTIVE",
        )
    )
    db.commit()


def main() -> None:
    db_url = os.getenv("DATABASE_URL", "sqlite:///./app_test.db")
    engine = create_engine(
        db_url,
        connect_args={"check_same_thread": False} if db_url.startswith("sqlite") else {},
    )

    # Ensure metadata has ALL models registered.
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        ensure_user(db, BUYER_EMAIL, BUYER_PASS, getattr(UserRole, "BUYER", "BUYER"))
        ensure_user(db, SELLER_EMAIL, SELLER_PASS, getattr(UserRole, "SELLER", "SELLER"))

        buyer = db.execute(select(User).where(User.email == BUYER_EMAIL)).scalar_one_or_none()
        seller = db.execute(select(User).where(User.email == SELLER_EMAIL)).scalar_one_or_none()

        print(f"USING_HASH_FN = {HASH_FN_NAME}")
        print(f"DATABASE_URL = {db_url}")
        print(f"SEEDED buyer={bool(buyer)} seller={bool(seller)}")

    print("OK: schema created & users seeded")


if __name__ == "__main__":
    main()

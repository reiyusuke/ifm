from __future__ import annotations

import os
import sys
from pathlib import Path

# ------------------------------------------------------------
# Make sure we can import `app.*` regardless of where we run from
# ------------------------------------------------------------
API_ROOT = Path(__file__).resolve().parents[1]  # .../apps/api
sys.path.insert(0, str(API_ROOT))

from sqlalchemy import select  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.db.session import engine  # noqa: E402
from app.models.models import User, UserRole  # noqa: E402

# password hashing helper (project-dependent)
HASH_FN_NAME = None
get_password_hash = None

try:
    # your earlier project used this path at some point
    from app.auth.security import get_password_hash as _fn  # type: ignore
    get_password_hash = _fn
    HASH_FN_NAME = "app.auth.security.get_password_hash"
except Exception:
    pass

if get_password_hash is None:
    try:
        # your current auth.py imports from app.security
        from app.security import get_password_hash as _fn  # type: ignore
        get_password_hash = _fn
        HASH_FN_NAME = "app.security.get_password_hash"
    except Exception:
        pass

if get_password_hash is None:
    raise RuntimeError("Cannot find password hash function (get_password_hash). Check app.security / app.auth.security.")

BUYER_EMAIL = os.getenv("E2E_BUYER_EMAIL", "realbuyer@ifm.com").strip().lower()
BUYER_PASS = os.getenv("E2E_BUYER_PASS", "buyerpass")

SELLER_EMAIL = os.getenv("E2E_SELLER_EMAIL", "realseller@ifm.com").strip().lower()
SELLER_PASS = os.getenv("E2E_SELLER_PASS", "sellerpass")


def ensure_user(db: Session, email: str, password: str, role: str) -> None:
    u = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if u:
        return
    db.add(
        User(
            email=email,
            password_hash=get_password_hash(password),  # type: ignore[misc]
            role=role,
            status="ACTIVE",
        )
    )
    db.commit()


def main() -> None:
    # Create tables if not exist (assuming your models are imported via app.models.models)
    # If your project uses Alembic migrations in CI, you can replace this with alembic upgrade.
    from app.db.base import Base  # noqa: E402

    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        ensure_user(db, BUYER_EMAIL, BUYER_PASS, UserRole.BUYER.value)
        ensure_user(db, SELLER_EMAIL, SELLER_PASS, UserRole.SELLER.value)

    print(f"USING_HASH_FN = {HASH_FN_NAME}")
    print("OK: schema created & users seeded")


if __name__ == "__main__":
    main()

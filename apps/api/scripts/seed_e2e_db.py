from __future__ import annotations

import os
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import engine
from app.db.base import Base  # Base をここから持ってくる構成のはず
from app.models.models import User, UserRole
from app.auth.security import get_password_hash


def main() -> None:
    # スキーマ作成
    Base.metadata.create_all(bind=engine)

    # テストで使うユーザー（tests/test_e2e_recommended.py に合わせる）
    buyer_email = os.getenv("E2E_BUYER_EMAIL", "realbuyer@ifm.com").strip().lower()
    buyer_pass = os.getenv("E2E_BUYER_PASS", "buyerpass")

    seller_email = os.getenv("E2E_SELLER_EMAIL", "realseller@ifm.com").strip().lower()
    seller_pass = os.getenv("E2E_SELLER_PASS", "sellerpass")

    with Session(engine) as db:
        # buyer
        u = db.execute(select(User).where(User.email == buyer_email)).scalar_one_or_none()
        if not u:
            db.add(
                User(
                    email=buyer_email,
                    password_hash=get_password_hash(buyer_pass),
                    role=UserRole.BUYER.value if hasattr(UserRole.BUYER, "value") else "BUYER",
                    status="ACTIVE",
                )
            )

        # seller
        u = db.execute(select(User).where(User.email == seller_email)).scalar_one_or_none()
        if not u:
            db.add(
                User(
                    email=seller_email,
                    password_hash=get_password_hash(seller_pass),
                    role=UserRole.SELLER.value if hasattr(UserRole.SELLER, "value") else "SELLER",
                    status="ACTIVE",
                )
            )

        db.commit()

    print("OK: schema created & users seeded")


if __name__ == "__main__":
    main()

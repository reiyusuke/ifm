from __future__ import annotations

from sqlalchemy import select
from app.db.session import SessionLocal, engine
from app.models.models import Base, User, UserRole, UserStatus
from app.security import get_password_hash


def init_db() -> None:
    # create tables
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # already seeded?
        existing = db.execute(select(User.id).limit(1)).scalar_one_or_none()
        if existing:
            return

        users = [
            User(
                email="realbuyer@ifm.com",
                password_hash=get_password_hash("buyerpass"),
                role=UserRole.BUYER,
                status=UserStatus.ACTIVE,
            ),
            User(
                email="buyer2@ifm.com",
                password_hash=get_password_hash("buyer2pass"),
                role=UserRole.BUYER,
                status=UserStatus.ACTIVE,
            ),
            User(
                email="seller@ifm.com",
                password_hash=get_password_hash("sellerpass"),
                role=UserRole.SELLER,
                status=UserStatus.ACTIVE,
            ),
        ]

        db.add_all(users)
        db.commit()
    finally:
        db.close()

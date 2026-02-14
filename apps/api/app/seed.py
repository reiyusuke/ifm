from __future__ import annotations

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.models import User, Idea, UserRole, UserStatus, IdeaStatus


def seed_demo_users(db: Session) -> None:
    if db.execute(select(User)).first():
        return

    buyer = User(
        email="buyer@example.com",
        password_hash="password",
        role=UserRole.BUYER,
        status=UserStatus.ACTIVE,
    )

    seller = User(
        email="seller@example.com",
        password_hash="password",
        role=UserRole.SELLER,
        status=UserStatus.ACTIVE,
    )

    db.add_all([buyer, seller])
    db.commit()


def seed_demo_ideas(db: Session) -> None:
    if db.execute(select(Idea)).first():
        return

    seller = db.execute(
        select(User).where(User.email == "seller@example.com")
    ).scalar_one()

    demo_ideas = [
        Idea(
            title="Demo Idea A",
            summary="Short summary A",
            body="Full body A",
            price=1000,
            resale_allowed=True,
            exclusive_option_price=999.0,
            status=IdeaStatus.ACTIVE,
            total_score=90,
            seller_id=seller.id,
        ),
        Idea(
            title="Demo Idea B",
            summary="Short summary B",
            body="Full body B",
            price=800,
            resale_allowed=True,
            exclusive_option_price=None,
            status=IdeaStatus.ACTIVE,
            total_score=80,
            seller_id=seller.id,
        ),
    ]

    db.add_all(demo_ideas)
    db.commit()


def seed_all(db: Session) -> None:
    seed_demo_users(db)
    seed_demo_ideas(db)

from __future__ import annotations

from sqlalchemy.orm import Session

from app.security import get_password_hash
from app.models.models import User, Idea, UserRole, UserStatus, IdeaStatus


DEMO_PASSWORD = "password"


def seed_demo_users(db: Session) -> None:
    demos = [
        ("buyer@example.com", UserRole.BUYER),
        ("seller@example.com", UserRole.SELLER),
    ]

    for email, role in demos:
        u = db.query(User).filter(User.email == email).first()
        hashed = get_password_hash(DEMO_PASSWORD)

        if u is None:
            u = User(
                email=email,
                role=role,
                status=UserStatus.ACTIVE,
                password_hash=hashed,
            )
            db.add(u)
        else:
            # 既存の壊れた hash を強制修復（平文や未知形式→bcryptへ）
            u.role = role
            u.status = UserStatus.ACTIVE
            u.password_hash = hashed

    db.commit()


def seed_demo_ideas(db: Session) -> None:
    seller = db.query(User).filter(User.email == "seller@example.com").first()
    if seller is None:
        return

    # すでに入ってたら何もしない（必要なら条件変えてOK）
    exists = db.query(Idea).count()
    if exists:
        return

    demo = [
        dict(
            title="Demo Idea A",
            summary="Demo summary A",
            body="Demo body A",
            price=500.0,
            resale_allowed=True,
            exclusive_option_price=999.0,
            status=IdeaStatus.PUBLISHED,
            total_score=90.0,
            seller_id=seller.id,
        ),
        dict(
            title="Demo Idea B",
            summary="Demo summary B",
            body="Demo body B",
            price=400.0,
            resale_allowed=True,
            exclusive_option_price=None,
            status=IdeaStatus.PUBLISHED,
            total_score=80.0,
            seller_id=seller.id,
        ),
    ]

    db.add_all([Idea(**d) for d in demo])
    db.commit()


def seed_all(db: Session) -> None:
    seed_demo_users(db)
    seed_demo_ideas(db)

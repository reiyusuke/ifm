from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.models import (
    User,
    Idea,
    UserRole,
    UserStatus,
    IdeaStatus,
)
from app.security import hash_password


def _get_user_by_email(db: Session, email: str) -> User | None:
    return db.execute(select(User).where(User.email == email)).scalar_one_or_none()


def seed_demo_users(db: Session) -> None:
    demo = [
        {"email": "buyer@example.com", "password": "password", "role": UserRole.BUYER},
        {"email": "seller@example.com", "password": "password", "role": UserRole.SELLER},
    ]

    changed = False
    for d in demo:
        u = _get_user_by_email(db, d["email"])
        if u is None:
            u = User(
                email=d["email"],
                password_hash=hash_password(d["password"]),
                role=d["role"],
                status=UserStatus.ACTIVE,
            )
            db.add(u)
            changed = True
        else:
            if not getattr(u, "password_hash", None):
                u.password_hash = hash_password(d["password"])
                changed = True
            if getattr(u, "role", None) != d["role"]:
                u.role = d["role"]
                changed = True
            if getattr(u, "status", None) != UserStatus.ACTIVE:
                u.status = UserStatus.ACTIVE
                changed = True

    if changed:
        db.commit()


def seed_demo_ideas(db: Session) -> None:
    # 既に1件でもあれば何もしない
    existing = db.execute(select(Idea.id).limit(1)).scalar_one_or_none()
    if existing is not None:
        return

    seller = _get_user_by_email(db, "seller@example.com")
    if seller is None:
        seller = User(
            email="seller@example.com",
            password_hash=hash_password("password"),
            role=UserRole.SELLER,
            status=UserStatus.ACTIVE,
        )
        db.add(seller)
        db.commit()
        db.refresh(seller)

    # ★ summary は NOT NULL。必ず文字列を入れる（body も保険で入れる）
    demo = [
        {
            "title": "Demo Idea A",
            "summary": "Demo summary A",
            "body": "Demo body A",
            "status": getattr(IdeaStatus.ACTIVE,'value','ACTIVE'),
            "total_score": 90.0,
            "exclusive_option_price": 999.0,
            "seller_id": seller.id,
        },
        {
            "title": "Demo Idea B",
            "summary": "Demo summary B",
            "body": "Demo body B",
            "status": getattr(IdeaStatus.ACTIVE,'value','ACTIVE'),
            "total_score": 80.0,
            "exclusive_option_price": None,
            "seller_id": seller.id,
        },
    ]

    db.add_all([Idea(**d) for d in demo])
    db.commit()


def seed_all(db: Session) -> None:
    seed_demo_users(db)
    seed_demo_ideas(db)

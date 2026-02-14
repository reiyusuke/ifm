from __future__ import annotations

from sqlalchemy.orm import Session

from app.security import hash_password
from app.models.models import (
    User, Idea,
    UserRole, UserStatus, IdeaStatus,
)

DEMO_PASSWORD = "password"

def seed_demo_users(db: Session) -> None:
    """
    既存ユーザーがいても必ず password_hash を修復する（これが重要）。
    """
    demo = [
        {
            "email": "buyer@example.com",
            "role": UserRole.BUYER,
            "status": UserStatus.ACTIVE,
        },
        {
            "email": "seller@example.com",
            "role": UserRole.SELLER,
            "status": UserStatus.ACTIVE,
        },
    ]

    for d in demo:
        u = db.query(User).filter(User.email == d["email"]).first()
        if u is None:
            u = User(
                email=d["email"],
                role=d["role"],
                status=d["status"],
                password_hash=hash_password(DEMO_PASSWORD),
            )
            db.add(u)
        else:
            # 既存が壊れてても強制で直す
            u.role = d["role"]
            u.status = d["status"]
            u.password_hash = hash_password(DEMO_PASSWORD)

    db.commit()

def seed_demo_ideas(db: Session) -> None:
    seller = db.query(User).filter(User.email == "seller@example.com").first()
    if seller is None:
        return

    demo = [
        {
            "id": 1,
            "title": "Demo Idea A",
            "summary": "Short demo summary A",
            "body": "Demo body A",
            "price": 0.0,
            "resale_allowed": True,
            "exclusive_option_price": 999.0,
            "status": IdeaStatus.ACTIVE,
            "total_score": 90.0,
            "seller_id": seller.id,
        },
        {
            "id": 2,
            "title": "Demo Idea B",
            "summary": "Short demo summary B",
            "body": "Demo body B",
            "price": 0.0,
            "resale_allowed": True,
            "exclusive_option_price": None,
            "status": IdeaStatus.ACTIVE,
            "total_score": 80.0,
            "seller_id": seller.id,
        },
    ]

    for d in demo:
        existing = db.query(Idea).filter(Idea.id == d["id"]).first()
        if existing is None:
            db.add(Idea(**d))
        else:
            # 必須項目は上書きして NOT NULL を回避
            for k, v in d.items():
                setattr(existing, k, v)

    db.commit()

def seed_all(db: Session) -> None:
    seed_demo_users(db)
    seed_demo_ideas(db)

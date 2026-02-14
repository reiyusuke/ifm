from __future__ import annotations

from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.models import User, UserRole, Idea, IdeaStatus
from app.security import hash_password


def seed_demo_users(db: Session) -> None:
    # seller@example.com / buyer@example.com を必ず作る（いなければ作成、いれば修復）
    seller = db.execute(select(User).where(User.email == "seller@example.com")).scalar_one_or_none()
    if seller is None:
        seller = User(
            email="seller@example.com",
            role=UserRole.SELLER,
            password_hash=hash_password("password"),
            created_at=datetime.utcnow(),
        )
        db.add(seller)
    else:
        # 既存でも password_hash が壊れてたら修復
        seller.role = UserRole.SELLER
        seller.password_hash = hash_password("password")

    buyer = db.execute(select(User).where(User.email == "buyer@example.com")).scalar_one_or_none()
    if buyer is None:
        buyer = User(
            email="buyer@example.com",
            role=UserRole.BUYER,
            password_hash=hash_password("password"),
            created_at=datetime.utcnow(),
        )
        db.add(buyer)
    else:
        buyer.role = UserRole.BUYER
        buyer.password_hash = hash_password("password")

    db.flush()  # id を確定


def seed_demo_ideas(db: Session) -> None:
    # seller を取得（なければ先に users seed が必要）
    seller = db.execute(select(User).where(User.email == "seller@example.com")).scalar_one()

    # Idea が 0 件ならデモ投入
    total = db.execute(select(Idea)).scalars().first()
    if total is not None:
        return

    demo = [
        Idea(
            title="Demo Idea A",
            summary="Demo summary A",
            description=None,
            is_exclusive=False,
            price=999.0,
            status=IdeaStatus.ACTIVE,
            total_score=90.0,
            seller_id=seller.id,
            created_at=datetime.utcnow(),
        ),
        Idea(
            title="Demo Idea B",
            summary="Demo summary B",
            description=None,
            is_exclusive=True,
            price=1999.0,
            status=IdeaStatus.ACTIVE,
            total_score=80.0,
            seller_id=seller.id,
            created_at=datetime.utcnow(),
        ),
    ]

    db.add_all(demo)


def seed_all(db: Session) -> None:
    # 失敗したら例外を投げて Render logs に出す（silent禁止）
    seed_demo_users(db)
    seed_demo_ideas(db)
    db.commit()

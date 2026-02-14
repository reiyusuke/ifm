from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.models import User, Idea, UserRole, IdeaStatus
from app.security import hash_password


def seed_demo_users(db: Session) -> None:
    # 既存ユーザーがいても password_hash は必ず直す（壊れhashで500になるのを潰す）
    seller = db.query(User).filter(User.email == "seller@example.com").first()
    buyer = db.query(User).filter(User.email == "buyer@example.com").first()

    if not seller:
        seller = User(email="seller@example.com", role=UserRole.SELLER, password_hash="")
        db.add(seller)

    if not buyer:
        buyer = User(email="buyer@example.com", role=UserRole.BUYER, password_hash="")
        db.add(buyer)

    db.commit()
    db.refresh(seller)
    db.refresh(buyer)

    # passwordを強制的に "password" へ揃える
    seller.password_hash = hash_password("password")
    buyer.password_hash = hash_password("password")
    db.commit()


def seed_demo_ideas(db: Session) -> None:
    seller = db.query(User).filter(User.email == "seller@example.com").first()
    if not seller:
        return

    exists = db.query(Idea).count()
    if exists >= 2:
        return

    demo = [
        dict(
            title="Demo Idea A",
            summary="Demo summary A",
            status=IdeaStatus.ACTIVE,
            total_score=90.0,
            exclusive_option_price=999.0,
            seller_id=seller.id,
        ),
        dict(
            title="Demo Idea B",
            summary="Demo summary B",
            status=IdeaStatus.ACTIVE,
            total_score=80.0,
            exclusive_option_price=None,
            seller_id=seller.id,
        ),
    ]

    db.add_all([Idea(**d) for d in demo])
    db.commit()


def seed_all(db: Session) -> None:
    seed_demo_users(db)
    seed_demo_ideas(db)

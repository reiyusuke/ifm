from __future__ import annotations

from sqlalchemy.orm import Session

from app.db import engine
from app.models.models import Base, User, Idea
from app.security import hash_password


def seed_all(db: Session) -> dict:
    # 0) テーブル作成（重要）
    Base.metadata.create_all(bind=engine)

    # 1) users が空なら demo user を作る
    if db.query(User).count() == 0:
        seller = User(
            email="seller@example.com",
            password_hash=hash_password("password"),
            role="SELLER",
            status="ACTIVE",
        )
        buyer = User(
            email="buyer@example.com",
            password_hash=hash_password("password"),
            role="BUYER",
            status="ACTIVE",
        )
        db.add_all([seller, buyer])
        db.commit()
        db.refresh(seller)
        db.refresh(buyer)

    # 2) seller を取得（無ければ作る）
    seller = db.query(User).filter(User.email == "seller@example.com").first()
    if seller is None:
        seller = User(
            email="seller@example.com",
            password_hash=hash_password("password"),
            role="SELLER",
            status="ACTIVE",
        )
        db.add(seller)
        db.commit()
        db.refresh(seller)

    # 3) ideas が空なら demo ideas を入れる
    if db.query(Idea).count() == 0:
        a = Idea(
            seller_id=seller.id,
            title="Demo Idea A",
            summary="Demo summary A",
            body="Demo body A",
            price=0.0,
            resale_allowed=True,
            exclusive_option_price=999.0,
            status="ACTIVE",
            total_score=90.0,
        )
        b = Idea(
            seller_id=seller.id,
            title="Demo Idea B",
            summary="Demo summary B",
            body="Demo body B",
            price=0.0,
            resale_allowed=True,
            exclusive_option_price=None,
            status="ACTIVE",
            total_score=80.0,
        )
        db.add_all([a, b])
        db.commit()

    # 返り値（任意）
    return {
        "users": db.query(User).count(),
        "ideas_total": db.query(Idea).count(),
        "ideas_active": db.query(Idea).filter(Idea.status == "ACTIVE").count(),
    }

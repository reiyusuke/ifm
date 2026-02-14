from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.models import Idea, IdeaStatus, User, UserRole, UserStatus


def seed_demo_users(db: Session) -> None:
    # 既に users が居れば何もしない
    if db.query(User).count() > 0:
        return

    buyer = User(
        email="buyer@example.com",
        password_hash="password",  # ★デモは平文運用（auth側の仕様に合わせる）
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
    # 既に ideas が居れば何もしない
    if db.query(Idea).count() > 0:
        return

    seller = db.query(User).filter(User.email == "seller@example.com").first()
    if not seller:
        return

    demo = [
        {
            "seller_id": seller.id,
            "title": "Demo Idea A",
            "summary": "Short demo summary A",  # ★NOT NULL
            "body": "Demo body A",
            "price": 0.0,
            "resale_allowed": True,
            "exclusive_option_price": 999.0,
            "status": IdeaStatus.ACTIVE,       # ★ACTIVE を使う実装に合わせる
            "total_score": 90.0,
        },
        {
            "seller_id": seller.id,
            "title": "Demo Idea B",
            "summary": "Short demo summary B",
            "body": "Demo body B",
            "price": 0.0,
            "resale_allowed": True,
            "exclusive_option_price": None,
            "status": IdeaStatus.ACTIVE,
            "total_score": 80.0,
        },
    ]

    db.add_all([Idea(**d) for d in demo])
    db.commit()


def seed_all(db: Session) -> None:
    seed_demo_users(db)
    seed_demo_ideas(db)

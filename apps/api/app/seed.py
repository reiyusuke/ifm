from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.models import Idea, User, UserRole, IdeaStatus
from app.security import hash_password


def seed_demo_users(db: Session) -> None:
    demo = [
        ("buyer@example.com", "password", UserRole.BUYER),
        ("seller@example.com", "password", UserRole.SELLER),
    ]

    for email, pw, role in demo:
        u = db.query(User).filter(User.email == email).first()
        if u:
            # 既存が壊れてても直す（平文/未知hash対策）
            u.password_hash = hash_password(pw)
            u.role = role
        else:
            db.add(
                User(
                    email=email,
                    password_hash=hash_password(pw),
                    role=role,
                )
            )


def seed_demo_ideas(db: Session) -> None:
    # demoユーザーがいないと作れない
    seller = db.query(User).filter(User.email == "seller@example.com").first()
    if not seller:
        return

    # 既に1件でもあれば「seed済み」とみなして何もしない（重複INSERTで落ちるのを防ぐ）
    if db.query(Idea).first() is not None:
        return

    demo = [
        Idea(
            title="Demo Idea A",
            summary="Demo summary A",
            description=None,
            price=999.0,
            is_exclusive=False,
            status=IdeaStatus.ACTIVE,
            total_score=90.0,
            seller_id=seller.id,
        ),
        Idea(
            title="Demo Idea B",
            summary="Demo summary B",
            description=None,
            price=1200.0,
            is_exclusive=True,
            status=IdeaStatus.ACTIVE,
            total_score=80.0,
            seller_id=seller.id,
        ),
    ]
    db.add_all(demo)


def seed_all(db: Session) -> None:
    try:
        seed_demo_users(db)
        seed_demo_ideas(db)
        db.commit()
    except IntegrityError:
        # 途中まで入ってる/再デプロイ等で重複した場合は落とさない
        db.rollback()
    except Exception:
        db.rollback()
        # startup を落としたくないので握っておく（main.py側でも握る）
        raise

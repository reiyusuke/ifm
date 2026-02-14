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
    """
    demoユーザーが無ければ作成。あれば最低限の項目を修復する。
    """
    demo = [
        {
            "email": "buyer@example.com",
            "password": "password",
            "role": UserRole.BUYER,
        },
        {
            "email": "seller@example.com",
            "password": "password",
            "role": UserRole.SELLER,
        },
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
            # 既存でも壊れてたら最低限修復
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
    """
    demoアイデアが0件のときだけ投入。
    ※ Idea モデルに存在しない key（例: description）は絶対に渡さない
    """
    existing = db.execute(select(Idea.id).limit(1)).scalar_one_or_none()
    if existing is not None:
        return

    seller = _get_user_by_email(db, "seller@example.com")
    if seller is None:
        # 念のため（通常ここには来ない）
        seller = User(
            email="seller@example.com",
            password_hash=hash_password("password"),
            role=UserRole.SELLER,
            status=UserStatus.ACTIVE,
        )
        db.add(seller)
        db.commit()
        db.refresh(seller)

    demo = [
        {
            "title": "Demo Idea A",
            "status": IdeaStatus.ACTIVE,
            "total_score": 90.0,
            "exclusive_option_price": 999.0,
            "seller_id": seller.id,
        },
        {
            "title": "Demo Idea B",
            "status": IdeaStatus.ACTIVE,
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

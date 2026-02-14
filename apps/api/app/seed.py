from __future__ import annotations

from sqlalchemy.orm import Session

# 既存のパスワードハッシュ関数があればそれを使う（auth側と完全一致させる）
def _hash_password(password: str) -> str:
    try:
        # 例: app/routers/auth.py に get_password_hash がある想定
        from app.routers.auth import get_password_hash  # type: ignore
        return get_password_hash(password)
    except Exception:
        # フォールバック（bcrypt）
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        return pwd_context.hash(password)


def seed_demo_users(db: Session) -> None:
    from app.models.models import User, UserRole, UserStatus  # type: ignore

    demo = [
        ("buyer@example.com", UserRole.BUYER),
        ("seller@example.com", UserRole.SELLER),
    ]

    pw_hash = _hash_password("password")

    for email, role in demo:
        u = db.query(User).filter(User.email == email).one_or_none()
        if u is None:
            u = User(
                email=email,
                role=role,
                status=getattr(UserStatus, "ACTIVE", "ACTIVE"),
                password_hash=pw_hash,
            )
            db.add(u)
        else:
            # 既存がいても、ログインできるように強制で合わせる
            u.role = role
            if hasattr(u, "status"):
                u.status = getattr(UserStatus, "ACTIVE", "ACTIVE")
            if hasattr(u, "password_hash"):
                u.password_hash = pw_hash

    db.commit()


def seed_demo_ideas(db: Session) -> None:
    """
    /ideas/recommended が空にならない最低限の seed。
    既に ideas があるなら何もしない。
    """
    from app.models.models import Idea, IdeaStatus  # type: ignore

    exists = db.query(Idea).first()
    if exists:
        return

    demo_ideas = [
        dict(
            title="Demo Idea A",
            summary="Demo summary A",
            body="Demo body A",
            price=100,
            resale_allowed=True,
            exclusive_option_price=999.0,
            total_score=90,
            status=getattr(IdeaStatus, "SUBMITTED", "SUBMITTED"),
            seller_id=1,  # demo seller を想定（IDは後で補正）
        ),
        dict(
            title="Demo Idea B",
            summary="Demo summary B",
            body="Demo body B",
            price=100,
            resale_allowed=True,
            exclusive_option_price=None,
            total_score=80,
            status=getattr(IdeaStatus, "SUBMITTED", "SUBMITTED"),
            seller_id=1,
        ),
    ]

    # seller_id を seller@example.com の実IDに合わせる
    from app.models.models import User  # type: ignore
    seller = db.query(User).filter(User.email == "seller@example.com").one_or_none()
    if seller:
        for d in demo_ideas:
            d["seller_id"] = seller.id

    for d in demo_ideas:
        db.add(Idea(**d))

    db.commit()


def seed_all(db: Session) -> None:
    seed_demo_users(db)
    seed_demo_ideas(db)

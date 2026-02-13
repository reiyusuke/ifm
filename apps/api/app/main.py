from __future__ import annotations

from fastapi import FastAPI
from sqlalchemy import select

from app.db.session import engine, SessionLocal
from app.models.models import User, Idea
from app.security import get_password_hash

from app.routers.auth import router as auth_router
from app.routers.ideas import router as ideas_router
from app.routers.deals import router as deals_router

# optional routers (存在しない場合があるので安全にimport)
try:
    from app.routers.me import router as me_router  # type: ignore
except Exception:
    me_router = None

try:
    from app.routers.admin import router as admin_router  # type: ignore
except Exception:
    admin_router = None


app = FastAPI()


def _seed_if_empty() -> None:
    """
    Render(本番)では初回起動時にDBが空になりやすいので、
    最低限のユーザー/アイデアを投入して動作確認できる状態にする。
    """
    db = SessionLocal()
    try:
        # --- users ---
        existing_users = db.execute(select(User.id).limit(1)).first()
        if not existing_users:
            buyer = User(
                email="buyer@example.com",
                password_hash=get_password_hash("password"),
                role="BUYER",
                status="ACTIVE",
            )
            seller = User(
                email="seller@example.com",
                password_hash=get_password_hash("password"),
                role="SELLER",
                status="ACTIVE",
            )
            db.add_all([buyer, seller])
            db.commit()
            db.refresh(buyer)
            db.refresh(seller)
            seller_id = int(seller.id)
        else:
            # seller を取る（なければ buyer でもOK）
            s = db.execute(select(User).where(User.role == "SELLER")).scalar_one_or_none()
            if s is None:
                s = db.execute(select(User).limit(1)).scalar_one()
            seller_id = int(s.id)

        # --- ideas ---
        existing_ideas = db.execute(select(Idea.id).limit(1)).first()
        if not existing_ideas:
            ideas = [
                Idea(
                    title="Demo Idea A",
                    total_score=90,
                    exclusive_option_price=999,
                    price=0,
                    seller_id=seller_id,
                ),
                Idea(
                    title="Demo Idea B",
                    total_score=75,
                    exclusive_option_price=None,
                    price=0,
                    seller_id=seller_id,
                ),
                Idea(
                    title="Demo Idea C",
                    total_score=60,
                    exclusive_option_price=1999,
                    price=0,
                    seller_id=seller_id,
                ),
            ]
            db.add_all(ideas)
            db.commit()
    finally:
        db.close()


@app.on_event("startup")
def _startup() -> None:
    # テーブル作成（既存なら何もしない）
    from app.models import models  # noqa: F401  (models importでmetadata登録)
    models.Base.metadata.create_all(bind=engine)

    # 初期データ投入
    _seed_if_empty()


@app.get("/health")
def health() -> dict:
    return {"ok": True}


app.include_router(auth_router)
app.include_router(ideas_router)
app.include_router(deals_router)

if me_router is not None:
    app.include_router(me_router)

if admin_router is not None:
    app.include_router(admin_router)

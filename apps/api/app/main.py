from __future__ import annotations

import os
import logging
from fastapi import FastAPI

from sqlalchemy.orm import Session

from app.db.session import engine
from app.models.models import Base, User, Idea

from app.routers.auth import router as auth_router
from app.routers.ideas import router as ideas_router
from app.routers.deals import router as deals_router

# optional routers
try:
    from app.routers.me import router as me_router
except Exception:
    me_router = None

try:
    from app.routers.admin import router as admin_router
except Exception:
    admin_router = None


logger = logging.getLogger("ifm")
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="ifm")


def _seed_prod_db(db: Session) -> None:
    """
    - 既存データがあれば何もしない
    - seed 失敗でもアプリは落とさない（rollbackして継続）
    """
    try:
        # ---- users (存在チェックのみ。既存があれば触らない) ----
        buyer = db.query(User).filter(User.email == "buyer@example.com").one_or_none()
        if buyer is None:
            buyer = User(
                email="buyer@example.com",
                # 既存があるならここは使われない。無い場合のみ作る。
                # ※password検証が必要なら、ここはあなたの get_password_hash() で作るのが本筋
                password_hash="$2b$12$gJg6Jb6u7WmG7uKj7n8l9eQqzqQ9t9p7a0mZzjJQ2oZs9w9i1kM0C",
                role="BUYER",
            )
            if hasattr(buyer, "status") and getattr(buyer, "status") is None:
                try:
                    buyer.status = "ACTIVE"
                except Exception:
                    pass
            db.add(buyer)
            db.commit()

        seller = db.query(User).filter(User.email == "seller@example.com").one_or_none()
        if seller is None:
            seller = User(
                email="seller@example.com",
                password_hash="$2b$12$gJg6Jb6u7WmG7uKj7n8l9eQqzqQ9t9p7a0mZzjJQ2oZs9w9i1kM0C",
                role="SELLER",
            )
            if hasattr(seller, "status") and getattr(seller, "status") is None:
                try:
                    seller.status = "ACTIVE"
                except Exception:
                    pass
            db.add(seller)
            db.commit()

        # ---- ideas ----
        # すでに1件でもあれば seed しない
        if db.query(Idea).limit(1).first() is not None:
            logger.info("seed: ideas already exist -> skip")
            return

        seller_id = int(getattr(seller, "id"))

        # ★重要: summary/body は NOT NULL の可能性があるので必ず文字列を入れる
        demo_ideas = [
            Idea(
                seller_id=seller_id,
                title="Demo Idea A",
                summary="Demo summary A",
                body="Demo body A",
                price=0,
                resale_allowed=False,
                exclusive_option_price=999,
                status="ACTIVE",
                total_score=90,
            ),
            Idea(
                seller_id=seller_id,
                title="Demo Idea B",
                summary="Demo summary B",
                body="Demo body B",
                price=0,
                resale_allowed=False,
                exclusive_option_price=None,
                status="ACTIVE",
                total_score=80,
            ),
        ]

        for it in demo_ideas:
            db.add(it)
        db.commit()
        logger.info("seed: demo ideas inserted")

    except Exception as e:
        db.rollback()
        logger.exception("seed failed (ignored): %s", e)


@app.on_event("startup")
def on_startup() -> None:
    # テーブル作成（idempotent）
    Base.metadata.create_all(bind=engine)

    # 必要なら Render 側で SEED_ON_STARTUP=0 にして無効化できる
    seed_on = os.getenv("SEED_ON_STARTUP", "1") == "1"
    if seed_on:
        with Session(bind=engine) as db:
            _seed_prod_db(db)


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

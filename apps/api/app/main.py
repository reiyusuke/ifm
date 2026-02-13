from __future__ import annotations

import logging
import os

from fastapi import FastAPI
from sqlalchemy.orm import Session

from app.db.session import engine
from app.models.models import Base, Idea, User
from app.security import get_password_hash

from app.routers.auth import router as auth_router
from app.routers.deals import router as deals_router
from app.routers.resale import router as resale_router
from app.routers.ideas import router as ideas_router

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


def _ensure_demo_users(db: Session) -> tuple[User, User]:
    """
    buyer/seller を必ず存在させ、さらに password_hash を "password" に必ず揃える。
    """
    pw_hash = get_password_hash("password")

    # buyer
    buyer = db.query(User).filter(User.email == "buyer@example.com").one_or_none()
    if buyer is None:
        buyer = User(email="buyer@example.com", password_hash=pw_hash, role="BUYER")
        db.add(buyer)
        db.commit()
        db.refresh(buyer)
        logger.info("seed: created buyer")
    else:
        if getattr(buyer, "password_hash", None) != pw_hash:
            buyer.password_hash = pw_hash
            db.commit()
            logger.info("seed: updated buyer password_hash")

    # seller
    seller = db.query(User).filter(User.email == "seller@example.com").one_or_none()
    if seller is None:
        seller = User(email="seller@example.com", password_hash=pw_hash, role="SELLER")
        db.add(seller)
        db.commit()
        db.refresh(seller)
        logger.info("seed: created seller")
    else:
        if getattr(seller, "password_hash", None) != pw_hash:
            seller.password_hash = pw_hash
            db.commit()
            logger.info("seed: updated seller password_hash")

    # user.status がある場合のみ触る（Enum不一致でも落とさない）
    for u in (buyer, seller):
        if hasattr(u, "status"):
            try:
                if getattr(u, "status") is None:
                    # ここは環境によって Enum が違う可能性があるので、失敗しても無視
                    u.status = "ACTIVE"
                    db.commit()
            except Exception:
                pass

    return buyer, seller


def _ensure_demo_ideas(db: Session, seller: User) -> None:
    """
    何も無ければ demo ideas を入れる（summary/body は NOT NULL 対策で必ず入れる）
    Idea.status は Enum に合わせて SUBMITTED を使う（DRAFT/SUBMITTED/ARCHIVED）
    """
    if db.query(Idea).limit(1).first() is not None:
        logger.info("seed: ideas already exist -> skip")
        return

    seller_id = int(getattr(seller, "id"))
    demo_ideas = [
        Idea(
            seller_id=seller_id,
            title="Demo Idea A",
            summary="Demo summary A",
            body="Demo body A",
            price=0,
            resale_allowed=False,
            exclusive_option_price=999,
            status="SUBMITTED",
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
            status="SUBMITTED",
            total_score=80,
        ),
    ]
    for it in demo_ideas:
        db.add(it)
    db.commit()
    logger.info("seed: inserted demo ideas")


@app.on_event("startup")
def on_startup() -> None:
    # まずテーブル作成
    Base.metadata.create_all(bind=engine)

    # --- DB constraint: only one exclusive deal per idea ---
    try:
        from sqlalchemy import text
        with engine.begin() as conn:
            conn.execute(text(
                "CREATE UNIQUE INDEX IF NOT EXISTS ux_deals_exclusive_per_idea "
                "ON deals(idea_id) WHERE is_exclusive = 1"
            ))
        logger.info("db: ensured ux_deals_exclusive_per_idea")
    except Exception as e:
        logger.exception("db: index create failed (ignored): %s", e)

    # 起動時 seed（Render用）
    if os.getenv("SEED_ON_STARTUP", "1") == "1":
        try:
            with Session(bind=engine) as db:
                _buyer, seller = _ensure_demo_users(db)
                _ensure_demo_ideas(db, seller)
        except Exception as e:
            logger.exception("startup seed failed (ignored): %s", e)


@app.get("/health")
def health() -> dict:
    return {"ok": True}


app.include_router(auth_router)
app.include_router(ideas_router)
app.include_router(deals_router)
app.include_router(resale_router)

if me_router is not None:
    app.include_router(me_router)

if admin_router is not None:
    app.include_router(admin_router)

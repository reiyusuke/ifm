from __future__ import annotations

import os
from datetime import datetime

from fastapi import FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import Base, engine, SessionLocal

# create_all 前にモデル import（metadata 登録）
from app.models import models as _models  # noqa: F401
from app.models import resale_listing as _resale_listing  # noqa: F401

from app.routers import auth, ideas, deals, resale
from app.seed import seed_all

app = FastAPI()


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()
    try:
        seed_all(db)  # 失敗したら例外で落ちる想定
    finally:
        db.close()


app.include_router(auth.router)
app.include_router(ideas.router)
app.include_router(deals.router)
app.include_router(resale.router)


@app.get("/health")
def health():
    return {
        "ok": True,
        "utc": datetime.utcnow().isoformat(),
        "render_git_commit": os.getenv("RENDER_GIT_COMMIT"),
    }


@app.get("/_debug/dbinfo")
def dbinfo():
    url = str(engine.url)

    # deals/ideas の存在と件数を “同一接続” で確認
    with engine.begin() as conn:
        # sqlite の場合
        if url.startswith("sqlite"):
            ideas = conn.execute(text("SELECT COUNT(*) FROM ideas")).scalar_one() if _table_exists(conn, "ideas") else None
            deals = conn.execute(text("SELECT COUNT(*) FROM deals")).scalar_one() if _table_exists(conn, "deals") else None
        else:
            # postgres 等でも同じSQLでOK（テーブル無ければ例外回避）
            ideas = _safe_count(conn, "ideas")
            deals = _safe_count(conn, "deals")

    return {
        "engine_url": url,
        "cwd": os.getcwd(),
        "files": sorted([f for f in os.listdir(".") if f.endswith(".db") or f.endswith(".sqlite")]),
        "ideas_count_same_conn": ideas,
        "deals_count_same_conn": deals,
    }


def _safe_count(conn, table: str):
    try:
        return conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar_one()
    except Exception:
        return None


def _table_exists(conn, name: str) -> bool:
    try:
        rows = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name=:n"), {"n": name}).fetchall()
        return len(rows) > 0
    except Exception:
        return False

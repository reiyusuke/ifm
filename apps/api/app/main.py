from __future__ import annotations

import os
from datetime import datetime

from fastapi import FastAPI
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
    # 1) テーブル作成
    Base.metadata.create_all(bind=engine)

    # 2) seed（失敗したら落として Render logs に理由を出す）
    db: Session = SessionLocal()
    try:
        seed_all(db)
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

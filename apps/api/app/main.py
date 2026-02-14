from __future__ import annotations

from fastapi import FastAPI
from sqlalchemy import text

from app.db.session import Base, engine, SessionLocal

# ルーター
from app.routers import auth, ideas, deals, resale

# ★重要: create_all の前に「モデル定義」を必ず import して Base に登録させる
# (import だけでOK。参照しなくても良い)
from app.models import models  # noqa: F401
from app.models import resale_listing  # noqa: F401

from app.seed import seed_all

app = FastAPI()


@app.on_event("startup")
def on_startup() -> None:
    # テーブル生成
    Base.metadata.create_all(bind=engine)

    # 起動確認ログ（Renderで見える）
    with engine.begin() as c:
        tables = c.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        ).fetchall()
        print("DB tables:", [t[0] for t in tables])

    # demo seed
    db = SessionLocal()
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
    return {"ok": True}

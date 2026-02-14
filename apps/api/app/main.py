from __future__ import annotations

import os

from fastapi import FastAPI
from sqlalchemy import text

from app.db.session import Base, engine

# ★ 重要：create_all の前にモデルを必ず import する
# これが無いと Base.metadata にテーブルが登録されず、create_all しても作られない
import app.models.models  # noqa: F401
import app.models.resale_listing  # noqa: F401

from app.routers import auth, ideas, deals, resale  # noqa: E402


app = FastAPI()


@app.on_event("startup")
def on_startup() -> None:
    # 1) DB URL をログに出す（Renderで「どのDB」を見てるか確定させる）
    db_url = os.getenv("DATABASE_URL", "sqlite:///./app.db")
    print(f"[startup] DATABASE_URL={db_url}")

    # 2) create_all 実行
    Base.metadata.create_all(bind=engine)
    print("[startup] Base.metadata.create_all done")

    # 3) 実際に “そのDB” に存在するテーブル一覧をログに出す（最重要）
    try:
        with engine.connect() as conn:
            if db_url.startswith("sqlite"):
                rows = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")).fetchall()
                print("[startup] sqlite tables:", [r[0] for r in rows])
            else:
                # postgres想定：public schema
                rows = conn.execute(
                    text("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename")
                ).fetchall()
                print("[startup] postgres tables:", [r[0] for r in rows])
    except Exception as e:
        print("[startup] table list failed:", repr(e))


# ルーター登録
app.include_router(auth.router)
app.include_router(ideas.router)
app.include_router(deals.router)
app.include_router(resale.router)


@app.get("/health")
def health():
    return {"ok": True}

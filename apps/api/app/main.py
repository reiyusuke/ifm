from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException
from sqlalchemy import text

from app.db import SessionLocal, engine
from app.models.models import Base
from app.routers import auth, ideas, deals, resale
from app.seed import seed_all

app = FastAPI()

# routers
app.include_router(auth.router)
app.include_router(ideas.router)
app.include_router(deals.router)
app.include_router(resale.router)


@app.on_event("startup")
def on_startup():
    # 1) テーブルは常に作る（idempotent）
    Base.metadata.create_all(bind=engine)

    # 2) seed（空なら入れる）
    #    デモ用途ならデフォルトONが楽。嫌なら Render の環境変数で IFM_AUTO_SEED=0 にできる。
    auto_seed = os.getenv("IFM_AUTO_SEED", "1").lower() not in ("0", "false", "no")
    if auto_seed:
        db = SessionLocal()
        try:
            seed_all(db)
        except Exception as e:
            # デモなら起動失敗は避けたいので握りつぶし（原因調査したいなら raise に変えてOK）
            print(f"=== STARTUP seed failed (ignored): {type(e).__name__}: {e} ===")
        finally:
            db.close()


@app.get("/health")
def health():
    # Render deploy 確認
    commit = os.getenv("RENDER_GIT_COMMIT")
    out = {"ok": True}
    if commit:
        out["render_git_commit"] = commit
    return out


# debug endpoints（ALLOW_DEBUG=1 の時だけ）
if os.getenv("ALLOW_DEBUG", "0").lower() in ("1", "true", "yes"):
    @app.get("/_debug/dbinfo")
    def debug_dbinfo():
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return {"engine_url": str(engine.url)}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"dbinfo failed: {type(e).__name__}: {e}")

    @app.post("/_debug/seed")
    def debug_seed():
        db = SessionLocal()
        try:
            return {"ok": True, "after": seed_all(db)}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"seed failed: {type(e).__name__}: {e}")
        finally:
            db.close()

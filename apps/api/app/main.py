import os
from fastapi import FastAPI, HTTPException
from sqlalchemy import text

from app.routers import auth, ideas, deals, resale
from app.seed import seed_all
from app.db import SessionLocal

APP_NAME = os.getenv("APP_NAME", "ifM API")

# Render の git commit（Render 側で設定されることが多い）
RENDER_GIT_COMMIT = (
    os.getenv("RENDER_GIT_COMMIT")
    or os.getenv("RENDER_GIT_COMMIT_SHA")
    or os.getenv("GIT_COMMIT")
    or os.getenv("COMMIT_SHA")
)

# --- Guards ---
ALLOW_DEBUG = os.getenv("ALLOW_DEBUG", "false").lower() == "true"
ALLOW_STARTUP_SEED = os.getenv("ALLOW_STARTUP_SEED", "false").lower() == "true"

app = FastAPI(title=APP_NAME)


@app.get("/health")
def health():
    payload = {"ok": True}
    if RENDER_GIT_COMMIT:
        payload["render_git_commit"] = RENDER_GIT_COMMIT
    return payload


# --- Routers ---
app.include_router(auth.router)
app.include_router(ideas.router)
app.include_router(deals.router)
app.include_router(resale.router)


# --- Startup: seed (optional) ---
@app.on_event("startup")
def startup_seed():
    if not ALLOW_STARTUP_SEED:
        return

    db = SessionLocal()
    try:
        print("=== STARTUP: seeding begin ===")
        seed_all(db)
        print("=== STARTUP: seeding done ===")
    except Exception as e:
        # 本番で落とさない
        print(f"=== STARTUP: seed failed (ignored): {type(e).__name__}: {e} ===")
    finally:
        db.close()


# --- DEBUG endpoints (guarded) ---
if ALLOW_DEBUG:

    @app.get("/_debug/dbinfo")
    def debug_dbinfo():
        """
        DB接続先や sqlite のテーブル存在・件数を返す（デバッグ用）
        """
        db = SessionLocal()
        try:
            # ここは "同一コネクションで数える" ことで、SQLite の別ファイル/別CWD問題の切り分けに使う
            total = db.execute(text("SELECT COUNT(*) FROM ideas")).scalar() or 0
            active = db.execute(text("SELECT COUNT(*) FROM ideas WHERE status='ACTIVE'")).scalar() or 0

            # sqlite_master で ideas テーブル確認
            rows = db.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='ideas'")
            ).fetchall()
            ideas_table_exists = len(rows) > 0

            # DB URL（SessionLocal が使ってるエンジンの URL を拾う）
            # SessionLocal.bind が無い場合でも落とさない
            engine_url = None
            try:
                bind = getattr(db, "get_bind", None)
                if callable(bind):
                    engine_url = str(db.get_bind().url)
                else:
                    engine_url = str(db.bind.url)  # type: ignore[attr-defined]
            except Exception:
                engine_url = "unknown"

            return {
                "engine_url": engine_url,
                "is_sqlite": (engine_url or "").startswith("sqlite"),
                "sqlite_ideas_table_exists": ideas_table_exists,
                "counts_same_conn": {"total": int(total), "active": int(active)},
                "render_git_commit": RENDER_GIT_COMMIT,
                "allow_debug": True,
                "allow_startup_seed": ALLOW_STARTUP_SEED,
            }
        finally:
            db.close()

    @app.post("/_debug/seed")
    def debug_seed():
        """
        seed を手動実行（デバッグ用）
        """
        db = SessionLocal()
        try:
            seed_all(db)
            total = db.execute(text("SELECT COUNT(*) FROM ideas")).scalar() or 0
            active = db.execute(text("SELECT COUNT(*) FROM ideas WHERE status='ACTIVE'")).scalar() or 0
            return {"ok": True, "after": {"total": int(total), "active": int(active)}}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"seed failed: {type(e).__name__}: {e}")
        finally:
            db.close()

else:
    # debug ルートは完全に存在しない（404）状態にする
    pass

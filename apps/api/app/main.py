from __future__ import annotations

import os
from fastapi import FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import Base, engine, SessionLocal

# create_all 前にモデルを import して metadata に載せる
from app.models import models as _models  # noqa: F401
from app.models import resale_listing as _resale_listing  # noqa: F401

from app.routers import auth, ideas, deals, resale
from app.seed import seed_all

app = FastAPI()


def _ensure_sqlite_columns() -> None:
    url = str(engine.url)
    if not url.startswith("sqlite"):
        return
    with engine.begin() as conn:
        cols = conn.execute(text("PRAGMA table_info(deals)")).fetchall()
        col_names = {r[1] for r in cols}
        if "amount" not in col_names:
            conn.execute(text("ALTER TABLE deals ADD COLUMN amount REAL"))


def _sqlite_table_exists(name: str) -> bool:
    url = str(engine.url)
    if not url.startswith("sqlite"):
        return False
    try:
        with engine.begin() as conn:
            rows = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name=:n"),
                {"n": name},
            ).fetchall()
            return len(rows) > 0
    except Exception:
        return False


def _counts_same_conn() -> dict:
    try:
        with engine.begin() as conn:
            total = conn.execute(text("SELECT COUNT(*) FROM ideas")).scalar() or 0
            active = conn.execute(
                text("SELECT COUNT(*) FROM ideas WHERE status = 'ACTIVE'")
            ).scalar() or 0
        return {"total": int(total), "active": int(active)}
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    _ensure_sqlite_columns()

    db: Session = SessionLocal()
    try:
        print("=== STARTUP: seeding begin ===")
        seed_all(db)
        print("=== STARTUP: seeding done ===")
    except Exception as e:
        print(f"=== STARTUP: seed failed (ignored): {type(e).__name__}: {e} ===")
    finally:
        db.close()


# routers
app.include_router(auth.router)
app.include_router(ideas.router)
app.include_router(deals.router)
app.include_router(resale.router)


@app.get("/health")
def health():
    return {
        "ok": True,
        "render_git_commit": os.getenv("RENDER_GIT_COMMIT"),
    }


@app.get("/_debug/dbinfo")
def debug_dbinfo():
    url = str(engine.url)
    return {
        "engine_url": url,
        "is_sqlite": url.startswith("sqlite"),
        "sqlite_ideas_table_exists": _sqlite_table_exists("ideas"),
        "counts_same_conn": _counts_same_conn(),
        "render_git_commit": os.getenv("RENDER_GIT_COMMIT"),
    }


@app.post("/_debug/seed")
def debug_seed():
    db: Session = SessionLocal()
    try:
        seed_all(db)
        after = _counts_same_conn()
        return {"ok": True, "after": after}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"seed failed: {type(e).__name__}: {e}"
        )
    finally:
        db.close()

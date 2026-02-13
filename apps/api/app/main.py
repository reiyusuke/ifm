from fastapi import FastAPI
from sqlalchemy import text

from app.db.session import engine

# routers
from app.routers import auth, ideas, deals, resale

app = FastAPI()

# --- ここでテーブルを確実に作る（Base経由が怪しいのでDDLで止血） ---
def _ensure_resale_table() -> None:
    ddl = """
    CREATE TABLE IF NOT EXISTS resale_listings (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      idea_id INTEGER NOT NULL,
      seller_id INTEGER NOT NULL,
      price REAL NOT NULL,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      UNIQUE(idea_id)
    );
    """
    with engine.begin() as conn:
        conn.execute(text(ddl))


@app.on_event("startup")
def _startup() -> None:
    _ensure_resale_table()


# --- routers ---
app.include_router(auth.router)
app.include_router(ideas.router)
app.include_router(deals.router)
app.include_router(resale.router)


@app.get("/health")
def health():
    return {"ok": True}

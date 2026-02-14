from __future__ import annotations

from fastapi import FastAPI

# DB
from app.db.session import Base, engine

# ルーター
from app.routers import auth, deals, ideas, resale

app = FastAPI()


@app.on_event("startup")
def on_startup() -> None:
    # 重要: create_all の前に「テーブル定義(モデル)」を必ず import する
    # これをしないと Base.metadata に載らず、テーブルが作られない
    from app.models.resale_listing import ResaleListing  # noqa: F401
    from app.models.models import Deal, Idea, User  # noqa: F401

    Base.metadata.create_all(bind=engine)


# ルーター登録
app.include_router(auth.router)
app.include_router(ideas.router)
app.include_router(deals.router)
app.include_router(resale.router)


@app.get("/health")
def health():
    return {"ok": True}

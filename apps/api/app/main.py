from __future__ import annotations

from fastapi import FastAPI

from app.db.session import Base, engine

# 重要: これを import しないと Base にモデルが登録されず create_all でテーブルが作られない
import app.models  # noqa: F401

from app.routers import auth, deals, ideas, resale

app = FastAPI()

# 起動時にテーブルを確実に作る（SQLiteでもRenderでも）
Base.metadata.create_all(bind=engine)

# ルーター登録
app.include_router(auth.router)
app.include_router(ideas.router)
app.include_router(deals.router)
app.include_router(resale.router)


@app.get("/health")
def health():
    return {"ok": True}

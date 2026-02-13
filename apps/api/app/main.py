from fastapi import FastAPI
from app.db.base import Base
from app.db.session import engine

# --- モデルを必ず import する（超重要） ---
from app.models import user, idea, deal, resale_listing  # noqa

from app.routers import auth, ideas, deals, resale

app = FastAPI()

# --- 起動時にテーブル作成 ---
Base.metadata.create_all(bind=engine)

# --- ルーター登録 ---
app.include_router(auth.router)
app.include_router(ideas.router)
app.include_router(deals.router)
app.include_router(resale.router)


@app.get("/health")
def health():
    return {"ok": True}

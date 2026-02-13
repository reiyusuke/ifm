from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.session import engine
from app.db.base import Base

# --- モデル import（重要：create_all に載せるため） ---
from app.models.user import User  # noqa: F401
from app.models.idea import Idea  # noqa: F401
from app.models.deal import Deal  # noqa: F401
from app.models.resale_listing import ResaleListing  # noqa: F401

# --- ルーター ---
from app.routers import auth
from app.routers import ideas
from app.routers import deals
from app.routers import resale

app = FastAPI()

# CORS（必要なら）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# DB テーブル作成（起動時）
Base.metadata.create_all(bind=engine)

# ルーター登録
app.include_router(auth.router)
app.include_router(ideas.router)
app.include_router(deals.router)
app.include_router(resale.router)


@app.get("/health")
def health():
    return {"ok": True}

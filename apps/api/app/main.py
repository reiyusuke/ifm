
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.session import Base, engine
from app import models  # モデルを読み込まないと create_all が効かない

from app.routers.auth import router as auth_router
from app.routers.ideas import router as ideas_router
from app.routers.deals import router as deals_router
from app.routers.me import router as me_router
from app.routers.admin import router as admin_router

app = FastAPI()

# -----------------------------------------------------------------------------
# DB 初期化（テスト用）
# -----------------------------------------------------------------------------
@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)

# -----------------------------------------------------------------------------
# CORS
# -----------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------------------------------
# Health
# -----------------------------------------------------------------------------
@app.get("/health")
def health():
    return {"ok": True}

# -----------------------------------------------------------------------------
# Routers
# -----------------------------------------------------------------------------
app.include_router(auth_router)
app.include_router(ideas_router)
app.include_router(deals_router)
app.include_router(me_router)
app.include_router(admin_router)


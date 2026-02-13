from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.session import engine
from app.models.models import Base

# Routers
from app.routers.auth import router as auth_router
from app.routers.ideas import router as ideas_router
from app.routers.deals import router as deals_router

try:
    from app.routers.me import router as me_router  # type: ignore
except Exception:
    me_router = None  # type: ignore

try:
    from app.routers.admin import router as admin_router  # type: ignore
except Exception:
    admin_router = None  # type: ignore


app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup() -> None:
    # Renderなど新規環境でテーブルが無い問題を防ぐ
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health() -> dict:
    return {"ok": True}


app.include_router(auth_router)
app.include_router(ideas_router)
app.include_router(deals_router)

if me_router is not None:
    app.include_router(me_router)

if admin_router is not None:
    app.include_router(admin_router)

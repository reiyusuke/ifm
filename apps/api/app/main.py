from fastapi import FastAPI

from app.db.session import engine
from app.models.models import Base

from app.routers.auth import router as auth_router
from app.routers.ideas import router as ideas_router
from app.routers.deals import router as deals_router

# optional routers
try:
    from app.routers.me import router as me_router
except Exception:
    me_router = None

try:
    from app.routers.admin import router as admin_router
except Exception:
    admin_router = None


app = FastAPI(title="ifm API")


@app.on_event("startup")
def on_startup():
    # Render / SQLite: create tables if they don't exist
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health():
    return {"ok": True}


app.include_router(auth_router)
app.include_router(ideas_router)
app.include_router(deals_router)

if me_router:
    app.include_router(me_router)

if admin_router:
    app.include_router(admin_router)

from fastapi import FastAPI

from app.db.session import engine
from app.models.models import Base
from app.models import models, resale_listing  # ← 重要（importで登録）
from app.routers import auth, ideas, deals, resale

app = FastAPI()

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

app.include_router(auth.router)
app.include_router(ideas.router)
app.include_router(deals.router)
app.include_router(resale.router)

@app.get("/health")
def health():
    return {"ok": True}

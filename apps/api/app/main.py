from __future__ import annotations

from fastapi import FastAPI
from sqlalchemy.orm import Session

from app.db.session import Base, engine, SessionLocal

# create_all 前にモデルを import
from app.models import models as _models  # noqa: F401
from app.models import resale_listing as _resale_listing  # noqa: F401

from app.routers import auth, ideas, deals, resale
from app.seed import seed_all

app = FastAPI()


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()
    try:
        try:
            seed_all(db)
        except Exception as e:
            # seed失敗でプロセス落とすと Render が死ぬので、ここは落とさない
            print(f"seed failed (ignored): {type(e).__name__}: {e}")
    finally:
        db.close()


app.include_router(auth.router)
app.include_router(ideas.router)
app.include_router(deals.router)
app.include_router(resale.router)


@app.get("/health")
def health():
    return {"ok": True}

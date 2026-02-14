from fastapi import FastAPI

from app.db.session import Base, engine

from app.routers import auth, deals, ideas, resale

# create_all の前に「テーブルを持つモデル定義」を必ず import して metadata に登録させる
from app.models import models as _models  # noqa: F401
from app.models import resale_listing as _resale_listing  # noqa: F401


app = FastAPI()


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


app.include_router(auth.router)
app.include_router(ideas.router)
app.include_router(deals.router)
app.include_router(resale.router)


@app.get("/health")
def health():
    return {"ok": True}

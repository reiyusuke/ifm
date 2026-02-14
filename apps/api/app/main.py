from fastapi import FastAPI

from app.db.session import Base, engine

# SQLAlchemy モデルを必ず import（create_all がテーブルを拾うため）
import app.models  # noqa: F401

from app.routers import auth, deals, ideas, resale

app = FastAPI()


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


# ルーター登録
app.include_router(auth.router)
app.include_router(ideas.router)
app.include_router(deals.router)
app.include_router(resale.router)


@app.get("/health")
def health():
    return {"ok": True}

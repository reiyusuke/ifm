from fastapi import FastAPI
from sqlalchemy.orm import Session

from app.db.session import engine, SessionLocal
from app.models.models import Base, User
from app.routers.auth import router as auth_router
from app.routers.ideas import router as ideas_router
from app.routers.deals import router as deals_router
from app.security import get_password_hash

app = FastAPI()


@app.on_event("startup")
def on_startup():
    # Create tables
    Base.metadata.create_all(bind=engine)

    # Seed a default buyer user if not exists
    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "buyer@example.com").first()
        if not user:
            db.add(
                User(
                    email="buyer@example.com",
                    password_hash=get_password_hash("password"),
                    role="BUYER",
                    status="ACTIVE",
                )
            )
            db.commit()
    finally:
        db.close()


@app.get("/health")
def health():
    return {"ok": True}


app.include_router(auth_router)
app.include_router(ideas_router)
app.include_router(deals_router)

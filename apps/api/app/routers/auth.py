from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.models import User
from app.security import create_access_token, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginReq(BaseModel):
    email: str
    password: str


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/login")
def login(req: LoginReq, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    if not user:
        raise HTTPException(status_code=401, detail="invalid credentials")

    if not verify_password(req.password, user.password_hash or ""):
        raise HTTPException(status_code=401, detail="invalid credentials")

    role_val = getattr(user.role, "value", user.role)
    token = create_access_token(
        data={
            "sub": str(user.id),         # ★ deps は sub を見る
            "role": str(role_val),       # "SELLER"/"BUYER" だけにする
        }
    )
    return {"access_token": token, "token_type": "bearer"}

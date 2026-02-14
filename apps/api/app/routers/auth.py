from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.models import User
from app.security import verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    # 1) user lookup
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        raise HTTPException(status_code=401, detail="invalid credentials")

    # 2) password verify
    if not verify_password(payload.password, getattr(user, "password_hash", None)):
        raise HTTPException(status_code=401, detail="invalid credentials")

    # 3) issue token
    # ★重要: sub= では呼ばない（既存実装差分で壊れるため）
    try:
        token = create_access_token(data={"sub": str(user.id), "role": str(getattr(user, "role", ""))})
    except Exception as e:
        # Renderで原因が追えるように detail に出す（今あなたが見てるやつ）
        raise HTTPException(status_code=500, detail=f"AUTH_LOGIN_FATAL: {type(e).__name__}: {e}")

    return {"access_token": token, "token_type": "bearer"}

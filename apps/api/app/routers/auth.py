from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.deps import get_db
from app.models.models import User
from app.security import create_access_token, verify_password


router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="invalid credentials")

    # role は必ず "SELLER"/"BUYER" のような value を入れる（Enum文字列を避ける）
    role_value = user.role.value if hasattr(user.role, "value") else str(user.role).split(".")[-1]

    try:
        token = create_access_token(data={"sub": str(user.id), "role": role_value})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AUTH_LOGIN_FATAL: {type(e).__name__}: {e}")

    return {"access_token": token, "token_type": "bearer"}

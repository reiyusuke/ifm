from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.models import User
from app.security import (
    ACCESS_TOKEN_MINUTES,
    ALGORITHM,
    SECRET_KEY,
    create_access_token,
    decode_access_token,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# pydantic schema は既存を使う前提（なければ最低限の型で通す）
try:
    from app.schemas.auth import LoginIn  # type: ignore
except Exception:
    from pydantic import BaseModel

    class LoginIn(BaseModel):
        email: str
        password: str


@router.post("/login")
def login(body: LoginIn, db: Session = Depends(get_db)):
    email = body.email.strip().lower()
    password = body.password

    user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="invalid credentials")

    if not verify_password(password, user.password_hash or ""):
        raise HTTPException(status_code=401, detail="invalid credentials")

    token = create_access_token(
        sub=str(user.id),
        role=str(user.role.value if hasattr(user.role, "value") else user.role),
        secret_key=SECRET_KEY,
        algorithm=ALGORITHM,
        expires_minutes=ACCESS_TOKEN_MINUTES,
    )
    return {"access_token": token, "token_type": "bearer"}


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    try:
        payload = decode_access_token(token, secret_key=SECRET_KEY, algorithm=ALGORITHM)
    except Exception:
        raise HTTPException(status_code=401, detail="not authenticated")

    sub = payload.get("sub")
    if not sub:
        raise HTTPException(status_code=401, detail="not authenticated")

    user = db.execute(select(User).where(User.id == int(sub))).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="not authenticated")

    return user

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.models import User
from app.security import create_access_token, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


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
        role=str(getattr(user.role, "value", user.role)),
    )
    return {"access_token": token, "token_type": "bearer"}

from __future__ import annotations

import traceback

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.models import User
from app.security import verify_password
from app.jwt import create_access_token  # 既存プロジェクトにある前提（JWT発行）


router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    # どこで落ちても必ずログに “原因” を出す
    try:
        user = db.query(User).filter(User.email == req.email).first()
        if user is None:
            raise HTTPException(status_code=401, detail="invalid credentials")

        # password_hash が None / 壊れてても verify_password は False を返す想定
        if not verify_password(req.password, getattr(user, "password_hash", "") or ""):
            raise HTTPException(status_code=401, detail="invalid credentials")

        token = create_access_token({"sub": str(user.id), "role": str(user.role)})
        return {"access_token": token, "token_type": "bearer"}

    except HTTPException:
        # 認証失敗はそのまま返す
        raise
    except Exception as e:
        print("AUTH_LOGIN_FATAL:", repr(e))
        traceback.print_exc()
        # 500のままにして、ログを確実に拾えるようにする
        raise HTTPException(status_code=500, detail="login failed")

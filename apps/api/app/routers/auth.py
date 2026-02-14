from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.models import User
from app.security import verify_password

# create_access_token の場所が揺れても動くようにする
create_access_token = None
_token_import_error = None

try:
    from app.jwt import create_access_token as _cat  # type: ignore
    create_access_token = _cat
except Exception as e1:
    try:
        from app.security import create_access_token as _cat2  # type: ignore
        create_access_token = _cat2
    except Exception as e2:
        _token_import_error = f"app.jwt import failed: {e1} / app.security import failed: {e2}"

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginIn(BaseModel):
    email: str
    password: str


@router.post("/login")
def login(payload: LoginIn):
    db: Session | None = None
    try:
        # 0) token関数が見つからない
        if create_access_token is None:
            raise HTTPException(status_code=500, detail=f"token function missing: {_token_import_error}")

        # 1) DB接続（Dependsを捨ててここで握る）
        db = SessionLocal()

        # 2) user lookup
        user = db.query(User).filter(User.email == payload.email).first()
        if user is None:
            raise HTTPException(status_code=401, detail="invalid credentials")

        # 3) password verify（verify_passwordが例外を飲んで False を返す想定）
        if not verify_password(payload.password, getattr(user, "password_hash", None)):
            raise HTTPException(status_code=401, detail="invalid credentials")

        # 4) token発行（ここで落ちても必ず JSON で返す）
        token = create_access_token(sub=str(user.id), role=getattr(user, "role", None))

        return {"access_token": token, "token_type": "bearer"}

    except HTTPException:
        # FastAPI標準のJSON: {"detail": "..."} で返る
        raise
    except Exception as e:
        # ここに来たら必ず JSON で原因文字列が返る
        raise HTTPException(status_code=500, detail=f"AUTH_LOGIN_FATAL: {type(e).__name__}: {e}")
    finally:
        if db is not None:
            db.close()

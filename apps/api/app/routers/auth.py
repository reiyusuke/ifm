from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.models import User
from app.security import verify_password

# create_access_token の場所が環境で揺れるので両対応
try:
    from app.jwt import create_access_token  # type: ignore
except Exception:
    try:
        from app.security import create_access_token  # type: ignore
    except Exception as e:
        create_access_token = None  # type: ignore
        _token_import_error = e
    else:
        _token_import_error = None
else:
    _token_import_error = None


router = APIRouter(prefix="/auth", tags=["auth"])


class LoginIn(BaseModel):
    email: str
    password: str


@router.post("/login")
def login(payload: LoginIn, db: Session = Depends(get_db)):
    # 1) token関数が無いなら、ここで明示的に落とす（Renderログで原因が見える）
    if create_access_token is None:
        raise HTTPException(status_code=500, detail=f"token function missing: {_token_import_error}")

    # 2) user lookup
    user = db.query(User).filter(User.email == payload.email).first()
    if user is None:
        raise HTTPException(status_code=401, detail="invalid credentials")

    # 3) password verify（例外は verify_password 側で False 扱い）
    if not verify_password(payload.password, getattr(user, "password_hash", None)):
        raise HTTPException(status_code=401, detail="invalid credentials")

    # 4) token発行（ここが500の本命なので try/except で握って “原因文字列” を返す）
    try:
        # sub は str が無難
        token = create_access_token(sub=str(user.id), role=getattr(user, "role", None))
    except Exception as e:
        # ここで 500 の中身が Render 側に出る（またはレスポンス detail で見える）
        raise HTTPException(status_code=500, detail=f"token issue: {type(e).__name__}: {e}")

    return {"access_token": token, "token_type": "bearer"}

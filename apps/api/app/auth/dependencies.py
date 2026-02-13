from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.auth.security import decode_token
from app.models.models import User, UserRole, UserStatus


def get_current_user(
    authorization: str | None = None,
    db: Session = Depends(get_db),
):
    """
    既存のルーター側で Authorization: Bearer <token> を使っている前提。
    FastAPIのHeader依存を避けるため、routers側で request.headers を取っている構成なら
    この関数は使われませんが、adminルーター用に最低限揃えます。
    """
    raise HTTPException(status_code=500, detail="use require_admin() with token dependency")


def require_admin(token: str = Depends(lambda: None), db: Session = Depends(get_db)):
    """
    admin.py から Depends(require_admin) で呼ばれる想定。
    既存のプロジェクトでは token の取り方が違う可能性があるので、
    admin.py側で Authorization header を直接受け取る形に合わせます。
    """
    raise HTTPException(status_code=500, detail="require_admin not wired")

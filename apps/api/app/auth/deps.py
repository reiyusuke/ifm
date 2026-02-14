from __future__ import annotations

from typing import Optional

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.models import User
from app.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _normalize_role(role: Optional[str]) -> Optional[str]:
    if not role:
        return role
    # "UserRole.SELLER" -> "SELLER"
    if "." in role:
        role = role.split(".")[-1]
    return role


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    if not token:
        raise HTTPException(status_code=401, detail="not authenticated")

    payload = decode_access_token(token)

    sub = payload.get("sub")
    if sub is None:
        raise HTTPException(status_code=401, detail="not authenticated")

    try:
        user_id = int(sub)
    except Exception:
        raise HTTPException(status_code=401, detail="not authenticated")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="not authenticated")

    # role はここで正規化しておく（必要なら他でも参照）
    user.role = getattr(user.role, "value", user.role)  # Enum -> value
    _ = _normalize_role(str(payload.get("role") or ""))  # side-effectなし、検証用

    return user

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Dict

import jwt
from fastapi import HTTPException
from passlib.context import CryptContext
from passlib.exc import UnknownHashError

# -----------------------------
# Password hashing
# -----------------------------
pwd_context = CryptContext(
    schemes=["bcrypt", "pbkdf2_sha256"],
    deprecated="auto",
)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# 互換: seed.py が hash_password を import している想定
# （別名を使っていた場合でも壊れないように）
def verify_password(plain_password: str, password_hash: str) -> bool:
    """
    壊れた hash（平文や未知形式）が DB に入っていても 500 にせず False を返す。
    """
    if not password_hash:
        return False
    try:
        return pwd_context.verify(plain_password, password_hash)
    except UnknownHashError:
        return False

# -----------------------------
# JWT settings
# -----------------------------
SECRET_KEY = os.getenv("SECRET_KEY", "dev_secret_change_me")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

def _now_utc() -> datetime:
    return datetime.now(timezone.utc)

def create_access_token(
    *,
    data: Optional[Dict[str, Any]] = None,
    sub: Optional[str] = None,
    role: Optional[str] = None,
    expires_delta: Optional[timedelta] = None,
    expires_minutes: Optional[int] = None,
) -> str:
    """
    互換性重視:
    - create_access_token(data={...})
    - create_access_token(sub="1", role="BUYER")
    - create_access_token(data={...}, expires_delta=...)
    どれでも動くようにする。
    """
    payload: Dict[str, Any] = {}
    if data:
        payload.update(dict(data))

    if sub is not None:
        payload["sub"] = str(sub)
    if role is not None:
        # Enum が来たら value/str へ
        payload["role"] = getattr(role, "value", role)

    if expires_delta is None:
        if expires_minutes is not None:
            expires_delta = timedelta(minutes=int(expires_minutes))
        else:
            expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    iat = _now_utc()
    exp = iat + expires_delta

    payload["iat"] = int(iat.timestamp())
    payload["exp"] = int(exp.timestamp())

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str) -> Dict[str, Any]:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="invalid token")

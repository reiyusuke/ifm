from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Any, Optional

import jwt
from fastapi import HTTPException
from passlib.context import CryptContext
from passlib.exc import UnknownHashError

# =========================
# Password hashing
# =========================
pwd_context = CryptContext(
    schemes=["pbkdf2_sha256", "bcrypt"],
    deprecated="auto",
)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, password_hash: Optional[str]) -> bool:
    if not password_hash:
        return False
    try:
        return pwd_context.verify(plain_password, password_hash)
    except UnknownHashError:
        return False


# =========================
# JWT
# =========================
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-me")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

def create_access_token(
    *,
    sub: Optional[str] = None,
    role: Optional[str] = None,
    data: Optional[dict[str, Any]] = None,
    expires_delta: Optional[timedelta] = None,
    **kwargs: Any,
) -> str:
    """
    互換性最優先:
      - create_access_token(sub="1", role="BUYER")
      - create_access_token(data={"sub":"1","role":"BUYER"})
      - create_access_token(data={"sub":"1"}, expires_delta=...)
    など「どの呼び方でも」壊れないようにする。
    """
    now = datetime.utcnow()
    expire = now + (expires_delta if expires_delta is not None else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))

    payload: dict[str, Any] = {}
    if data:
        payload.update(data)

    if sub is not None:
        payload["sub"] = str(sub)

    if role is not None:
        payload["role"] = role

    # 既に入ってる可能性もあるので上書き
    payload["iat"] = int(now.timestamp())
    payload["exp"] = int(expire.timestamp())

    # sub が最終的に無いのは許さない（トークンが意味をなさない）
    if "sub" not in payload or payload["sub"] in (None, ""):
        raise TypeError("create_access_token requires 'sub' (either via sub= or data['sub'])")

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str) -> dict[str, Any]:
    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if not isinstance(decoded, dict):
            raise HTTPException(status_code=401, detail="invalid token")
        return decoded
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="invalid token")

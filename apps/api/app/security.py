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
# 既存DBに混在しても安全にする（UnknownHashError は verify_password で False にする）
pwd_context = CryptContext(
    schemes=["pbkdf2_sha256", "bcrypt"],
    deprecated="auto",
)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, password_hash: Optional[str]) -> bool:
    """
    壊れた hash（平文や未知形式）が DB に入っていても 500 にせず False を返す。
    """
    if not password_hash:
        return False
    try:
        return pwd_context.verify(plain_password, password_hash)
    except UnknownHashError:
        return False


# =========================
# JWT
# =========================
# deps.py が import している名前を必ず提供する
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-me")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

def create_access_token(
    sub: str,
    role: Optional[str] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    now = datetime.utcnow()
    expire = now + (expires_delta if expires_delta is not None else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))

    payload: dict[str, Any] = {
        "sub": str(sub),
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    if role is not None:
        payload["role"] = role

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str) -> dict[str, Any]:
    """
    deps.py から呼ばれる前提。失敗したら HTTPException を投げる。
    """
    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if not isinstance(decoded, dict):
            raise HTTPException(status_code=401, detail="invalid token")
        return decoded
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="invalid token")

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import jwt
from fastapi import HTTPException
from jwt import PyJWTError
from passlib.context import CryptContext
from passlib.exc import UnknownHashError


# ============
# JWT settings
# ============
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-me")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # 24h


# =====================
# Password hashing
# =====================
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    if not password_hash:
        return False
    try:
        return pwd_context.verify(plain_password, password_hash)
    except UnknownHashError:
        # DB に平文/未知形式が入ってても 500 にしない
        return False


# =====================
# Helpers
# =====================
def _normalize_role(role: Any) -> str:
    """
    role を必ず "SELLER"/"BUYER"/"ADMIN" 形式に正規化する。
    - Enum -> .value があればそれを使う
    - "UserRole.SELLER" のような文字列 -> "SELLER" に落とす
    """
    if role is None:
        return ""

    # Enumっぽい場合（.value を持つ）
    val = getattr(role, "value", None)
    if isinstance(val, str):
        role = val

    # 文字列化
    s = str(role)

    # "UserRole.SELLER" / "Role.SELLER" などを "SELLER" にする
    if "." in s:
        s = s.split(".")[-1]

    return s


# =====================
# JWT create / decode
# =====================
def create_access_token(
    *,
    user_id: Any,
    role: Any,
    expires_minutes: Optional[int] = None,
) -> str:
    exp_mins = ACCESS_TOKEN_EXPIRE_MINUTES if expires_minutes is None else int(expires_minutes)
    now = datetime.now(timezone.utc)

    payload: Dict[str, Any] = {
        "sub": str(user_id),
        "role": _normalize_role(role),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=exp_mins)).timestamp()),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Dict[str, Any]:
    """
    失敗したらHTTPException(401)を投げる。roleも正規化して返す。
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except PyJWTError as e:
        raise HTTPException(status_code=401, detail=f"invalid token: {type(e).__name__}")

    # 正規化
    payload["role"] = _normalize_role(payload.get("role"))
    return payload

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Tuple

import jwt
from jwt import PyJWTError
from passlib.context import CryptContext

# ---- JWT settings ----
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # 24h

# ---- Password hashing ----
pwd_context = CryptContext(
    schemes=["pbkdf2_sha256"],  # これに統一（bcrypt絡み事故回避）
    deprecated="auto",
)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    if not password_hash:
        return False
    try:
        return pwd_context.verify(plain_password, password_hash)
    except Exception:
        # 壊れたhash等でも500にしない
        return False


def _normalize_role(role: Any) -> str:
    """
    roleがEnumでもstrでも必ず "SELLER" / "BUYER" / "ADMIN" の形にする
    """
    if role is None:
        return ""
    # Enumなら .value
    if hasattr(role, "value"):
        role = role.value
    role_str = str(role)

    # "UserRole.SELLER" みたいなのを "SELLER" に寄せる
    if "." in role_str:
        role_str = role_str.split(".")[-1]

    return role_str


def create_access_token(
    subject: str,
    role: Any,
    expires_delta: Optional[timedelta] = None,
) -> str:
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))

    payload: Dict[str, Any] = {
        "sub": str(subject),
        "role": _normalize_role(role),
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Tuple[str, str]:
    """
    Returns (user_id, role). Raises if invalid.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        sub = payload.get("sub")
        role = payload.get("role")
        if not sub:
            raise ValueError("missing sub")
        return str(sub), str(role or "")
    except (PyJWTError, ValueError) as e:
        raise e

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import jwt
from passlib.context import CryptContext

# Single source of truth for JWT settings
SECRET_KEY = os.getenv("JWT_SECRET") or os.getenv("SECRET_KEY") or "dev-secret-dev-secret-dev-secret-devsecret"
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_MINUTES = int(os.getenv("ACCESS_TOKEN_MINUTES", "1440"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    if not password_hash:
        return False
    return pwd_context.verify(plain_password, password_hash)


def create_access_token(
    *,
    sub: str,
    role: str,
    secret_key: str = SECRET_KEY,
    algorithm: str = ALGORITHM,
    expires_minutes: int = ACCESS_TOKEN_MINUTES,
    extra_claims: Optional[Dict[str, Any]] = None,
) -> str:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=expires_minutes)

    payload: Dict[str, Any] = {
        "sub": sub,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }
    if extra_claims:
        payload.update(extra_claims)

    return jwt.encode(payload, secret_key, algorithm=algorithm)


def decode_access_token(
    token: str,
    *,
    secret_key: str = SECRET_KEY,
    algorithm: str = ALGORITHM,
) -> Dict[str, Any]:
    return jwt.decode(token, secret_key, algorithms=[algorithm])

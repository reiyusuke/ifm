from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
import time
from typing import Any, Dict, Optional

import jwt


# ------------------------------------------------------------
# JWT settings
# ------------------------------------------------------------
def _get_secret() -> str:
    # app/auth/jwt.py と同じ優先順位に寄せる（invalid token 回避）
    return (
        os.environ.get("JWT_SECRET")
        or os.environ.get("SECRET_KEY")
        or os.environ.get("APP_SECRET")
        or "dev-secret-change-me"
    )


ALGORITHM = os.getenv("JWT_ALG") or os.getenv("JWT_ALGORITHM") or "HS256"
ACCESS_TOKEN_EXPIRE_SECONDS = int(os.getenv("ACCESS_TOKEN_EXPIRE_SECONDS", str(60 * 60 * 24)))  # 24h


def create_access_token(*, sub: str, role: str, expires_seconds: Optional[int] = None) -> str:
    now = int(time.time())
    exp = now + int(expires_seconds or ACCESS_TOKEN_EXPIRE_SECONDS)
    payload = {"sub": str(sub), "role": str(role), "iat": now, "exp": exp}
    return jwt.encode(payload, _get_secret(), algorithm=ALGORITHM)


def decode_access_token(token: str) -> Dict[str, Any]:
    # 例外は呼び出し側で HTTPException にする想定
    return jwt.decode(token, _get_secret(), algorithms=[ALGORITHM])


# ------------------------------------------------------------
# Password hashing (PBKDF2-SHA256, no external deps)
# Format: pbkdf2_sha256$<iters>$<salt_b64>$<dk_b64>
# ------------------------------------------------------------
_PBKDF2_ITERS = int(os.getenv("PBKDF2_ITERS", "200000"))


def hash_password(password: str) -> str:
    if password is None:
        raise ValueError("password is required")
    pw = password.encode("utf-8")
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", pw, salt, _PBKDF2_ITERS, dklen=32)
    salt_b64 = base64.urlsafe_b64encode(salt).decode("ascii").rstrip("=")
    dk_b64 = base64.urlsafe_b64encode(dk).decode("ascii").rstrip("=")
    return f"pbkdf2_sha256${_PBKDF2_ITERS}${salt_b64}${dk_b64}"


def verify_password(plain_password: str, password_hash: str) -> bool:
    try:
        algo, iters_s, salt_b64, dk_b64 = password_hash.split("$", 3)
        if algo != "pbkdf2_sha256":
            return False
        iters = int(iters_s)
        # padding を戻す
        salt = base64.urlsafe_b64decode(_pad_b64(salt_b64))
        expected = base64.urlsafe_b64decode(_pad_b64(dk_b64))

        dk = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, iters, dklen=len(expected))
        return hmac.compare_digest(dk, expected)
    except Exception:
        return False


def _pad_b64(s: str) -> str:
    return s + "=" * (-len(s) % 4)

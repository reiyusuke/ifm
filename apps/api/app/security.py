from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import jwt
from jwt import PyJWTError
from passlib.context import CryptContext


# NOTE:
# Renderで SECRET_KEY が未設定だと、デプロイ/再起動/複数インスタンスで鍵が変わり得て
# 発行した直後のトークンが別プロセスで検証できず 401 になる。
# 本番は必ず Render の Environment で SECRET_KEY を設定すること。
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    """
    壊れたハッシュ等が入っていても例外で 500 にしない。
    """
    if not password_hash:
        return False
    try:
        return pwd_context.verify(plain_password, password_hash)
    except Exception:
        return False


def _normalize_role(role: Any) -> Optional[str]:
    if role is None:
        return None
    s = str(role)
    # "UserRole.SELLER" → "SELLER"
    if "." in s:
        s = s.split(".")[-1]
    return s


def create_access_token(
    *,
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    to_encode = dict(data)

    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))

    # 互換のため iat/exp を入れる
    to_encode.update(
        {
            "iat": int(now.timestamp()),
            "exp": int(expire.timestamp()),
        }
    )

    # role が Enum でも必ず "SELLER"/"BUYER" になるよう補正
    if "role" in to_encode:
        to_encode["role"] = _normalize_role(to_encode["role"])

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Dict[str, Any]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except PyJWTError as e:
        raise ValueError(f"JWT_DECODE_ERROR: {type(e).__name__}: {e}") from e

    # role 正規化（受け側でも保険）
    if "role" in payload:
        payload["role"] = _normalize_role(payload.get("role"))

    return payload

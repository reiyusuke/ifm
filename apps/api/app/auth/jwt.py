"""
互換用モジュール。

過去に app/auth/jwt.py を参照している箇所があっても、
秘密鍵/アルゴリズムのズレで invalid token が起きないように、
実体は app/auth/security.py に寄せる。
"""

from typing import Any, Dict

from app.auth.security import create_access_token, decode_access_token


def encode(payload: Dict[str, Any]) -> str:
    return create_access_token(payload)


def decode(token: str) -> Dict[str, Any]:
    return decode_access_token(token)

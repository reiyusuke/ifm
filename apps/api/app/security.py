from __future__ import annotations

from passlib.context import CryptContext
from passlib.exc import UnknownHashError

# bcrypt を使わず、依存が軽い pbkdf2_sha256 を採用（Renderでのbcrypt事故回避）
pwd_context = CryptContext(
    schemes=["pbkdf2_sha256"],
    deprecated="auto",
)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    """
    壊れたhash（平文・未知形式）や、対応外形式でも 500 にせず False を返す。
    """
    if not password_hash:
        return False
    try:
        return pwd_context.verify(plain_password, password_hash)
    except UnknownHashError:
        return False
    except Exception:
        # ここで落ちて 500 になるのを防ぐ（bcrypt絡み等の想定外例外）
        return False

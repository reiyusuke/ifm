from __future__ import annotations

from passlib.context import CryptContext

pwd_context = CryptContext(
    schemes=["pbkdf2_sha256"],
    deprecated="auto",
)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, password_hash: str | None) -> bool:
    """
    壊れた hash（平文/未知形式/None）がDBに入っていても 500 にせず False を返す。
    """
    if not password_hash:
        return False
    try:
        return pwd_context.verify(plain_password, password_hash)
    except Exception:
        # UnknownHashError / ValueError / TypeError など全部ここで吸収
        return False

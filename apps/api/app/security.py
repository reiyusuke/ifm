from __future__ import annotations

from passlib.context import CryptContext
from passlib.exc import UnknownHashError

# bcrypt を標準に
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    """
    壊れた hash（平文や未知形式）が DB に入っていても 500 にせず False を返す。
    """
    if not password_hash:
        return False
    try:
        return pwd_context.verify(plain_password, password_hash)
    except UnknownHashError:
        return False

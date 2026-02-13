from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

# -----------------------
# Password hashing
# -----------------------
try:
    from passlib.context import CryptContext  # type: ignore

    _pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def get_password_hash(password: str) -> str:
        return _pwd_context.hash(password)

    def verify_password(plain_password: str, password_hash: str) -> bool:
        try:
            return _pwd_context.verify(plain_password, password_hash)
        except Exception:
            return False

except Exception:
    # Fallback (dev only): accept plain / "plain$xxx"
    def get_password_hash(password: str) -> str:
        return "plain$" + password

    def verify_password(plain_password: str, password_hash: str) -> bool:
        return password_hash == plain_password or password_hash == ("plain$" + plain_password)

# -----------------------
# JWT
# -----------------------
def _jwt_encode(payload: dict[str, Any], secret: str, algorithm: str) -> str:
    try:
        from jose import jwt  # type: ignore
        return jwt.encode(payload, secret, algorithm=algorithm)
    except Exception:
        import jwt  # type: ignore
        return jwt.encode(payload, secret, algorithm=algorithm)

def _jwt_decode(token: str, secret: str, algorithms: list[str]) -> dict[str, Any]:
    try:
        from jose import jwt  # type: ignore
        return jwt.decode(token, secret, algorithms=algorithms)
    except Exception:
        import jwt  # type: ignore
        return jwt.decode(token, secret, algorithms=algorithms)

def create_access_token(
    *,
    sub: str,
    role: str,
    secret_key: str,
    algorithm: str,
    expires_minutes: int = 60 * 24,
) -> str:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=expires_minutes)
    payload = {"sub": sub, "role": role, "iat": int(now.timestamp()), "exp": int(exp.timestamp())}
    return _jwt_encode(payload, secret_key, algorithm)

def decode_access_token(
    token: str,
    *,
    secret_key: str,
    algorithm: str,
) -> dict[str, Any]:
    return _jwt_decode(token, secret_key, [algorithm])

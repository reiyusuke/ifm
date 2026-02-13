from __future__ import annotations

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.models import User
from app.security import decode_access_token, SECRET_KEY, ALGORITHM

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    try:
        payload = decode_access_token(token, secret_key=SECRET_KEY, algorithm=ALGORITHM)
    except Exception:
        raise HTTPException(status_code=401, detail="not authenticated")

    sub = payload.get("sub")
    if not sub:
        raise HTTPException(status_code=401, detail="not authenticated")

    user = db.execute(select(User).where(User.id == int(sub))).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="not authenticated")

    return user

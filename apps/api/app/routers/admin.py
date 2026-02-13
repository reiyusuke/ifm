from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.db.session import get_db
from app.models.models import User

router = APIRouter(prefix="/admin", tags=["admin"])


def _require_admin(user: User) -> None:
    role = getattr(user.role, "value", user.role)
    if str(role).upper() != "ADMIN":
        raise HTTPException(status_code=403, detail="forbidden")


@router.get("/health")
def admin_health(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin(current_user)
    return {"ok": True}

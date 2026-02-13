from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.db.session import get_db
from app.models.models import User

router = APIRouter(prefix="/me", tags=["me"])


@router.get("")
def me(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # db は将来拡張用（不要なら消してOK）
    return {
        "id": int(current_user.id),
        "email": current_user.email,
        "role": str(getattr(current_user.role, "value", current_user.role)),
        "status": str(getattr(current_user.status, "value", current_user.status)),
    }

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.auth.deps import get_current_user
from app.models.models import Deal, UserRole

router = APIRouter(prefix="/me", tags=["me"])


def _require_auth(payload: Dict[str, Any]) -> None:
    if not payload or payload.get("sub") is None:
        raise HTTPException(status_code=401, detail="not authenticated")


def _require_role(payload: Dict[str, Any], role: str) -> None:
    role_val = payload.get("role")
    if role_val != role:
        raise HTTPException(status_code=403, detail=f"{role.lower()}s only")


class DealOut(BaseModel):
    deal_id: int
    idea_id: int
    title: str
    price: float
    is_exclusive: bool
    created_at: datetime


@router.get("/deals", response_model=List[DealOut])
def my_deals(
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    _require_auth(current_user)
    _require_role(current_user, UserRole.BUYER.value)

    buyer_id = int(current_user["sub"])

    deals = (
        db.execute(
            select(Deal)
            .where(Deal.buyer_id == buyer_id)
            .order_by(Deal.created_at.desc(), Deal.id.desc())
        )
        .scalars()
        .all()
    )

    out: List[DealOut] = []
    for d in deals:
        title = ""
        try:
            if getattr(d, "idea", None) is not None:
                title = str(getattr(d.idea, "title", ""))  # relationship 前提
        except Exception:
            title = ""

        out.append(
            DealOut(
                deal_id=int(d.id),
                idea_id=int(d.idea_id),
                title=title,
                price=float(getattr(d, "amount", 0.0) or 0.0),
                is_exclusive=bool(getattr(d, "is_exclusive", False)),
                created_at=getattr(d, "created_at"),
            )
        )
    return out

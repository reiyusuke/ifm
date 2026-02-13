from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.db.session import get_db
from app.models.models import Deal, Idea, User

router = APIRouter(prefix="/resale", tags=["resale"])


class ResaleListIn(BaseModel):
    idea_id: int
    price: int


class ResaleBuyIn(BaseModel):
    idea_id: int


def _get_exclusive_owner_deal(db: Session, idea_id: int) -> Deal | None:
    return (
        db.execute(
            select(Deal).where(
                Deal.idea_id == idea_id,
                Deal.is_exclusive == True,  # noqa: E712
            )
        )
        .scalars()
        .first()
    )


@router.post("/list")
def list_exclusive(
    body: ResaleListIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Exclusive owner only: list the exclusive for resale.
    We store listing as Deal.status = "LISTED" and Deal.amount = asking price.
    """
    deal = _get_exclusive_owner_deal(db, body.idea_id)
    if not deal:
        raise HTTPException(status_code=404, detail="exclusive not found")

    if deal.buyer_id != current_user.id:
        raise HTTPException(status_code=403, detail="not exclusive owner")

    # mark as listed
    if hasattr(deal, "status"):
        deal.status = "LISTED"
    deal.amount = int(body.price)
    db.commit()
    return {"ok": True}


@router.post("/buy")
def buy_listed_exclusive(
    body: ResaleBuyIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Buy listed exclusive: transfer ownership by moving deal.buyer_id.
    """
    deal = _get_exclusive_owner_deal(db, body.idea_id)
    if not deal:
        raise HTTPException(status_code=404, detail="exclusive not found")

    if getattr(deal, "status", None) != "LISTED":
        raise HTTPException(status_code=409, detail="exclusive not listed")

    if deal.buyer_id == current_user.id:
        raise HTTPException(status_code=409, detail="already owner")

    # transfer
    deal.buyer_id = current_user.id
    if hasattr(deal, "status"):
        deal.status = "COMPLETED"
    db.commit()
    return {"ok": True}

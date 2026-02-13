from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
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


def _get_exclusive_deal(db: Session, idea_id: int) -> Deal | None:
    return (
        db.execute(
            select(Deal).where(Deal.idea_id == idea_id, Deal.is_exclusive == True)  # noqa: E712
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
    # idea exists?
    idea = db.execute(select(Idea).where(Idea.id == body.idea_id)).scalar_one_or_none()
    if not idea:
        raise HTTPException(status_code=404, detail="idea not found")

    # current user must own exclusive
    ex = _get_exclusive_deal(db, body.idea_id)
    if not ex or ex.buyer_id != current_user.id:
        raise HTTPException(status_code=404, detail="exclusive not found")

    # mark as listed + set asking price into amount (MVP)
    ex.status = "LISTED"
    ex.amount = int(body.price)
    db.commit()
    return {"ok": True}


@router.post("/buy")
def buy_exclusive(
    body: ResaleBuyIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Find listed exclusive deal (ONLY ONE ROW for this idea)
    listed = (
        db.execute(
            select(Deal).where(
                Deal.idea_id == body.idea_id,
                Deal.is_exclusive == True,  # noqa: E712
                Deal.status == "LISTED",
            )
        )
        .scalars()
        .first()
    )
    if not listed:
        raise HTTPException(status_code=404, detail="exclusive not listed")

    if listed.buyer_id == current_user.id:
        raise HTTPException(status_code=409, detail="already owner")

    # Buyer might already have a non-exclusive deal row for same idea.
    buyer_existing = (
        db.execute(
            select(Deal).where(
                Deal.buyer_id == current_user.id,
                Deal.idea_id == body.idea_id,
            )
        )
        .scalars()
        .first()
    )
    if buyer_existing and buyer_existing.is_exclusive:
        raise HTTPException(status_code=409, detail="already exclusive owner")

    # Transfer ownership by updating the SAME exclusive row (avoid unique constraint hit)
    try:
        if buyer_existing:
            db.delete(buyer_existing)  # keep "one row per buyer+idea" assumption

        listed.buyer_id = current_user.id
        listed.status = "COMPLETED"  # back to completed/owned
        # listed.amount stays as resale price (MVP)

        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="exclusive already taken")

    return {"ok": True}

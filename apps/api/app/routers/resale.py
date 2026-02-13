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
        db.execute(select(Deal).where(Deal.idea_id == idea_id, Deal.is_exclusive == True))  # noqa: E712
        .scalars()
        .first()
    )


def _get_buyer_deal(db: Session, buyer_id: int, idea_id: int) -> Deal | None:
    return (
        db.execute(select(Deal).where(Deal.buyer_id == buyer_id, Deal.idea_id == idea_id))
        .scalars()
        .first()
    )


@router.post("/list")
def list_resale(
    body: ResaleListIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Exclusive owner only can list for resale.
    (MVP) We store listing on Idea.resale_price + Idea.resale_active if fields exist.
    """
    ex = _get_exclusive_deal(db, body.idea_id)
    if not ex:
        raise HTTPException(status_code=404, detail="exclusive not found")

    if ex.buyer_id != current_user.id:
        raise HTTPException(status_code=403, detail="not exclusive owner")

    idea = db.execute(select(Idea).where(Idea.id == body.idea_id)).scalar_one_or_none()
    if not idea:
        raise HTTPException(status_code=404, detail="idea not found")

    # store listing if fields exist
    if hasattr(idea, "resale_price"):
        setattr(idea, "resale_price", int(body.price))
    if hasattr(idea, "resale_active"):
        setattr(idea, "resale_active", True)
    if hasattr(idea, "resale_status"):
        setattr(idea, "resale_status", "LISTED")

    db.commit()
    return {"ok": True}


@router.post("/buy")
def buy_resale(
    body: ResaleBuyIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Transfer exclusive Deal to buyer.
    Important: If buyer already has a non-exclusive Deal for same (buyer_id, idea_id),
    delete it first to avoid UNIQUE(buyer_id, idea_id) conflict.
    """
    idea = db.execute(select(Idea).where(Idea.id == body.idea_id)).scalar_one_or_none()
    if not idea:
        raise HTTPException(status_code=404, detail="idea not found")

    # listing check (if fields exist)
    if hasattr(idea, "resale_active") and not bool(getattr(idea, "resale_active")):
        raise HTTPException(status_code=409, detail="not listed")

    ex = _get_exclusive_deal(db, body.idea_id)
    if not ex:
        raise HTTPException(status_code=404, detail="exclusive not found")

    # buyer already has a deal?
    buyer_deal = _get_buyer_deal(db, current_user.id, body.idea_id)
    if buyer_deal and bool(buyer_deal.is_exclusive):
        raise HTTPException(status_code=409, detail="already purchased")

    # delete buyer's non-exclusive row to prevent (buyer_id,idea_id) unique conflict
    if buyer_deal and (not bool(buyer_deal.is_exclusive)):
        db.delete(buyer_deal)
        db.flush()

    # transfer exclusive ownership
    ex.buyer_id = current_user.id

    # clear listing (if fields exist)
    if hasattr(idea, "resale_active"):
        setattr(idea, "resale_active", False)
    if hasattr(idea, "resale_status"):
        setattr(idea, "resale_status", "SOLD")

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        # most likely: unique(buyer_id,idea_id) or other constraint
        raise HTTPException(status_code=409, detail="resale transfer conflict")

    return {"ok": True}

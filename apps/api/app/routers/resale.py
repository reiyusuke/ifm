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


def _get_exclusive_deal(db: Session, idea_id: int, buyer_id: int) -> Deal | None:
    return (
        db.execute(
            select(Deal).where(
                Deal.idea_id == idea_id,
                Deal.buyer_id == buyer_id,
                Deal.is_exclusive == True,  # noqa: E712
            )
        )
        .scalar_one_or_none()
    )


def _get_listed_exclusive(db: Session, idea_id: int) -> Deal | None:
    # 「出品中」の exclusive deal を探す（status は文字列想定）
    return (
        db.execute(
            select(Deal).where(
                Deal.idea_id == idea_id,
                Deal.is_exclusive == True,  # noqa: E712
                Deal.status == "LISTED",
            )
        )
        .scalar_one_or_none()
    )


@router.get("/market")
def market(db: Session = Depends(get_db)):
    """
    Return all listed exclusive deals.

    Response item fields:
    - idea_id
    - title
    - price
    """
    rows = db.execute(
        select(Deal, Idea)
        .join(Idea, Idea.id == Deal.idea_id)
        .where(
            Deal.is_exclusive == True,  # noqa: E712
            Deal.status == "LISTED",
        )
        .order_by(Deal.idea_id.asc())
    ).all()

    out = []
    for deal, idea in rows:
        out.append(
            {
                "idea_id": int(deal.idea_id),
                "title": getattr(idea, "title", ""),
                "price": int(getattr(deal, "amount", 0) or 0),
            }
        )
    return out


@router.post("/list")
def list_for_resale(
    body: ResaleListIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List an exclusive deal for resale.

    Rules:
    - must be exclusive owner => 403
    - sets deal.status="LISTED"
    - sets deal.amount=price (use amount as resale price in this MVP)
    """
    deal = _get_exclusive_deal(db, body.idea_id, current_user.id)
    if not deal:
        raise HTTPException(status_code=404, detail="exclusive not found")

    deal.status = "LISTED"
    deal.amount = int(body.price)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="exclusive already taken")

    return {"ok": True}


@router.post("/buy")
def buy_resale(
    body: ResaleBuyIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Buy a listed exclusive deal.

    Rules:
    - must exist as LISTED => 404 (exclusive not found)
    - if buyer already has exclusive => 409 already purchased
    - if buyer has non-exclusive deal => delete it before transfer
    - transfer by updating buyer_id on the listed row (no new row)
    """
    listed = _get_listed_exclusive(db, body.idea_id)
    if not listed:
        raise HTTPException(status_code=404, detail="exclusive not found")

    # buyer already has exclusive?
    already_excl = _get_exclusive_deal(db, body.idea_id, current_user.id)
    if already_excl:
        raise HTTPException(status_code=409, detail="already purchased")

    # delete buyer's non-exclusive (if exists) to avoid duplicates / tier confusion
    non_excl = (
        db.execute(
            select(Deal).where(
                Deal.idea_id == body.idea_id,
                Deal.buyer_id == current_user.id,
                Deal.is_exclusive == False,  # noqa: E712
            )
        )
        .scalar_one_or_none()
    )
    if non_excl:
        db.delete(non_excl)
        db.flush()

    # transfer ownership
    listed.buyer_id = current_user.id
    listed.status = "COMPLETED"

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="exclusive already taken")

    return {"ok": True}

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.db.session import get_db
from app.models.models import Deal, Idea, User

router = APIRouter(prefix="/deals", tags=["deals"])


class DealIn(BaseModel):
    idea_id: int
    is_exclusive: bool = False


def _calc_amount(idea: Idea, is_exclusive: bool) -> int:
    """
    deals.amount is NOT NULL => always return int.
    """
    if is_exclusive:
        price = getattr(idea, "exclusive_option_price", None)
        if price is None:
            raise HTTPException(status_code=400, detail="exclusive option not available")
        return int(price)

    for attr in ("price", "base_price", "standard_price", "non_exclusive_price"):
        v = getattr(idea, attr, None)
        if v is not None:
            return int(v)

    return 0


@router.post("")
def create_or_update_deal(
    body: DealIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Purchase / upgrade deal.

    Rules:
    - If idea.exclusive_option_price is null, is_exclusive=true => 400
    - First purchase creates a deal
    - If already purchased non-exclusive, is_exclusive=true upgrades (if available)
    - Downgrade (exclusive -> non-exclusive) is forbidden => 409
    - Re-buy same tier => 409
    """
    idea = db.execute(select(Idea).where(Idea.id == body.idea_id)).scalar_one_or_none()
    if not idea:
        raise HTTPException(status_code=404, detail="idea not found")

    amount = _calc_amount(idea, bool(body.is_exclusive))

    deal = (
        db.execute(
            select(Deal).where(
                Deal.buyer_id == current_user.id,
                Deal.idea_id == body.idea_id,
            )
        )
        .scalar_one_or_none()
    )

    # New purchase
    if not deal:
        deal = Deal(
            buyer_id=current_user.id,
            idea_id=body.idea_id,
            amount=amount,  # NOT NULL
            is_exclusive=bool(body.is_exclusive),
        )
        if hasattr(deal, "status") and getattr(deal, "status") is None:
            try:
                deal.status = "COMPLETED"
            except Exception:
                pass

        db.add(deal)
        db.commit()
        return {"ok": True, "upgraded": False}

    # Existing purchase
    if deal.is_exclusive and not body.is_exclusive:
        # テスト期待の文言に合わせる
        raise HTTPException(status_code=409, detail="cannot downgrade exclusive")

    # Upgrade path
    if (not deal.is_exclusive) and body.is_exclusive:
        deal.is_exclusive = True
        deal.amount = amount
        db.commit()
        return {"ok": True, "upgraded": True}

    # Same tier re-purchase
    raise HTTPException(status_code=409, detail="already purchased")

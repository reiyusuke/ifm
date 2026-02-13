from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, desc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.db.session import get_db
from app.models.models import Deal, Idea, User
from app.models.resale_listing import ResaleListing

router = APIRouter(prefix="/resale", tags=["resale"])


class ResaleListIn(BaseModel):
    idea_id: int
    price: int


class ResaleBuyIn(BaseModel):
    idea_id: int


def _get_exclusive_deal_for_seller(db: Session, idea_id: int, seller_id: int) -> Deal | None:
    return (
        db.execute(
            select(Deal).where(
                Deal.idea_id == idea_id,
                Deal.buyer_id == seller_id,
                Deal.is_exclusive == True,  # noqa: E712
            )
        )
        .scalars()
        .first()
    )


@router.post("/list")
def resale_list(
    body: ResaleListIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # seller が exclusive owner でないと出品できない
    deal = _get_exclusive_deal_for_seller(db, body.idea_id, current_user.id)
    if not deal:
        raise HTTPException(status_code=403, detail="not exclusive owner")

    if body.price <= 0:
        raise HTTPException(status_code=400, detail="invalid price")

    # 既存の listing があれば上書き（idea_id は UNIQUE）
    listing = (
        db.execute(select(ResaleListing).where(ResaleListing.idea_id == body.idea_id))
        .scalars()
        .first()
    )
    if listing:
        listing.seller_id = current_user.id
        listing.price = int(body.price)
    else:
        listing = ResaleListing(
            idea_id=body.idea_id,
            seller_id=current_user.id,
            price=int(body.price),
        )
        db.add(listing)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="already listed")

    return {"ok": True}


@router.get("/market")
def resale_market(db: Session = Depends(get_db)):
    # マーケットに出てるもの一覧（新しい順）
    rows = db.execute(
        select(ResaleListing, Idea)
        .join(Idea, Idea.id == ResaleListing.idea_id)
        .order_by(desc(ResaleListing.created_at), desc(ResaleListing.id))
    ).all()

    out = []
    for listing, idea in rows:
        out.append(
            {
                "idea_id": listing.idea_id,
                "title": getattr(idea, "title", ""),
                "total_score": int(getattr(idea, "total_score", 0) or 0),
                "price": int(listing.price),
                "seller_id": int(listing.seller_id),
                "listed_at": listing.created_at.isoformat() if listing.created_at else None,
            }
        )
    return out


@router.post("/buy")
def resale_buy(
    body: ResaleBuyIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # listing 取得
    listing = (
        db.execute(select(ResaleListing).where(ResaleListing.idea_id == body.idea_id))
        .scalars()
        .first()
    )
    if not listing:
        raise HTTPException(status_code=404, detail="not listed")

    # seller の exclusive deal を取得
    deal = _get_exclusive_deal_for_seller(db, body.idea_id, int(listing.seller_id))
    if not deal:
        # listing が残骸になってるケース
        db.delete(listing)
        db.commit()
        raise HTTPException(status_code=404, detail="exclusive not found")

    # buyer がすでに同じ idea を持ってたら購入不可（仕様に合わせる）
    existing = (
        db.execute(
            select(Deal).where(Deal.idea_id == body.idea_id, Deal.buyer_id == current_user.id)
        )
        .scalars()
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="already purchased")

    # transfer：exclusive deal の buyer_id を買い手へ付け替え
    deal.buyer_id = current_user.id

    # listing は削除
    db.delete(listing)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="exclusive already taken")

    return {"ok": True}

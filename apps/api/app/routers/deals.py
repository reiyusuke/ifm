from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.auth.deps import get_current_user
from app.models.models import Deal, Idea, UserRole

router = APIRouter(prefix="/deals", tags=["deals"])


def _require_auth(payload: Dict[str, Any]) -> None:
    if not payload or payload.get("sub") is None:
        raise HTTPException(status_code=401, detail="not authenticated")


def _require_role(payload: Dict[str, Any], role: str) -> None:
    if payload.get("role") != role:
        raise HTTPException(status_code=403, detail=f"{role.lower()}s only")


def _as_int(v: Any) -> int:
    try:
        return int(v)
    except Exception:
        raise HTTPException(status_code=400, detail="invalid id")


class DealCreateIn(BaseModel):
    idea_id: int = Field(..., ge=1)
    is_exclusive: bool = False


class DealCreateOut(BaseModel):
    ok: bool
    deal_id: int
    already_owned: bool
    upgraded: bool


@router.post("", response_model=DealCreateOut)
def create_deal(
    body: DealCreateIn,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    BUYER の購入 API

    仕様:
    - 初回購入:
        - is_exclusive=false で通常購入
        - is_exclusive=true で独占購入（exclusive_option_price がある場合のみ）
    - 2回目以降:
        - 通常 -> 独占 は upgrade として許可（同一 deal レコードを更新）
        - 独占 -> 通常 は **不可**（409 Conflict）
        - 同条件の再POSTは冪等（already_owned=true で返す）
    """
    _require_auth(current_user)
    _require_role(current_user, UserRole.BUYER.value)

    buyer_id = _as_int(current_user["sub"])
    idea_id = int(body.idea_id)
    want_exclusive = bool(body.is_exclusive)

    # idea 取得
    idea: Optional[Idea] = (
        db.execute(select(Idea).where(Idea.id == idea_id)).scalars().first()
    )
    if idea is None:
        raise HTTPException(status_code=404, detail="idea not found")

    # ここはプロジェクトの仕様に合わせて調整可（今は SUBMITTED のみ購入可に寄せる）
    status_str = str(getattr(idea, "status", ""))
    if "SUBMITTED" not in status_str:
        raise HTTPException(status_code=400, detail="idea not purchasable")

    exclusive_price = getattr(idea, "exclusive_option_price", None)
    exclusive_available = exclusive_price is not None

    if want_exclusive and not exclusive_available:
        raise HTTPException(status_code=400, detail="exclusive option not available")

    # 既存 deal（buyer_id, idea_id）
    existing: Optional[Deal] = (
        db.execute(
            select(Deal).where(Deal.buyer_id == buyer_id, Deal.idea_id == idea_id)
        )
        .scalars()
        .first()
    )

    # 既に持ってる場合
    if existing is not None:
        already_owned = True
        is_exclusive_now = bool(getattr(existing, "is_exclusive", False))

        # 独占 -> 通常 は不可 (A案)
        if is_exclusive_now and not want_exclusive:
            raise HTTPException(status_code=409, detail="cannot downgrade exclusive")

        # 通常 -> 独占 upgrade
        if (not is_exclusive_now) and want_exclusive:
            if not exclusive_available:
                raise HTTPException(status_code=400, detail="exclusive option not available")
            existing.is_exclusive = True
            # amount を持ってる設計なら上書き（任意だが整合性のため）
            if hasattr(existing, "amount"):
                try:
                    existing.amount = float(exclusive_price)
                except Exception:
                    pass
            db.add(existing)
            db.commit()
            return DealCreateOut(ok=True, deal_id=int(existing.id), already_owned=True, upgraded=True)

        # それ以外（同条件の再POSTなど）は冪等で返す
        return DealCreateOut(ok=True, deal_id=int(existing.id), already_owned=already_owned, upgraded=False)

    # 新規作成
    amount = float(getattr(idea, "price", 0.0) or 0.0)
    if want_exclusive:
        amount = float(exclusive_price)

    deal = Deal(
        buyer_id=buyer_id,
        idea_id=idea_id,
        is_exclusive=want_exclusive,
        created_at=datetime.utcnow(),
    )
    if hasattr(deal, "amount"):
        try:
            deal.amount = amount
        except Exception:
            pass

    db.add(deal)

    # UNIQUE(buyer_id, idea_id) があるので競合は拾う
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        # 競合したら既存を読み直して既存扱いにする
        existing2: Optional[Deal] = (
            db.execute(
                select(Deal).where(Deal.buyer_id == buyer_id, Deal.idea_id == idea_id)
            )
            .scalars()
            .first()
        )
        if existing2 is None:
            raise HTTPException(status_code=500, detail="failed to create deal")

        # 競合時も A案適用
        is_exclusive_now = bool(getattr(existing2, "is_exclusive", False))
        if is_exclusive_now and not want_exclusive:
            raise HTTPException(status_code=409, detail="cannot downgrade exclusive")

        # 通常->独占 upgrade をここでも拾う
        if (not is_exclusive_now) and want_exclusive:
            if not exclusive_available:
                raise HTTPException(status_code=400, detail="exclusive option not available")
            existing2.is_exclusive = True
            if hasattr(existing2, "amount"):
                try:
                    existing2.amount = float(exclusive_price)
                except Exception:
                    pass
            db.add(existing2)
            db.commit()
            return DealCreateOut(ok=True, deal_id=int(existing2.id), already_owned=True, upgraded=True)

        return DealCreateOut(ok=True, deal_id=int(existing2.id), already_owned=True, upgraded=False)

    db.refresh(deal)
    return DealCreateOut(ok=True, deal_id=int(deal.id), already_owned=False, upgraded=False)

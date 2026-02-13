from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.db.session import get_db
from app.models.models import Idea, Deal, User

router = APIRouter(prefix="/ideas", tags=["ideas"])


@router.get("/recommended")
def recommended(
    include_owned: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ideas = (
        db.execute(
            select(Idea).where(Idea.status == "SUBMITTED")
        )
        .scalars()
        .all()
    )

    result = []

    for idea in ideas:
        deal = (
            db.execute(
                select(Deal).where(
                    Deal.buyer_id == current_user.id,
                    Deal.idea_id == idea.id,
                )
            )
            .scalars()
            .first()
        )

        is_owned = deal is not None
        owned_is_exclusive = bool(deal.is_exclusive) if deal else False

        # 🔥 exclusive が誰かに取られているか
        exclusive_taken = (
            db.query(Deal)
            .filter(Deal.idea_id == idea.id, Deal.is_exclusive == True)  # noqa
            .first()
            is not None
        )

        if not include_owned and is_owned:
            continue

        result.append(
            {
                "id": idea.id,
                "title": idea.title,
                "total_score": idea.total_score,
                "exclusive_option_price": idea.exclusive_option_price,
                "already_owned": is_owned,
                "owned_is_exclusive": owned_is_exclusive,
                "is_owned": is_owned,
                "exclusive_taken": exclusive_taken,
            }
        )

    # score降順
    result.sort(key=lambda x: x["total_score"], reverse=True)

    return result

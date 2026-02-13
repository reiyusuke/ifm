from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.db.session import get_db
from app.models.models import Deal, Idea, User

router = APIRouter(prefix="/ideas", tags=["ideas"])


@router.get("/recommended")
def recommended(
    include_owned: bool = Query(False, description="include ideas already owned by current user"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Recommended ideas.

    - default: exclude owned ideas
    - include_owned=true: include owned ideas and mark them already_owned=true
    - order: total_score desc
    """
    owned_subq = (
        select(Deal.idea_id.label("idea_id"), Deal.is_exclusive.label("owned_is_exclusive"))
        .where(Deal.buyer_id == current_user.id)
        .subquery()
    )

    stmt = (
        select(Idea, owned_subq.c.owned_is_exclusive)
        .outerjoin(owned_subq, owned_subq.c.idea_id == Idea.id)
        .order_by(desc(Idea.total_score))
    )

    if not include_owned:
        stmt = stmt.where(owned_subq.c.idea_id.is_(None))

    rows = db.execute(stmt).all()

    out = []
    for idea, owned_is_exclusive in rows:
        already_owned = owned_is_exclusive is not None

        exclusive_taken = (
            db.query(Deal)
            .filter(Deal.idea_id == idea.id, Deal.is_exclusive == True)  # noqa: E712
            .first()
            is not None
        )

        out.append(
            {
                "id": int(idea.id),
                "title": getattr(idea, "title", None),
                "total_score": int(getattr(idea, "total_score", 0) or 0),
                "exclusive_option_price": getattr(idea, "exclusive_option_price", None),
                "already_owned": bool(already_owned),
                "owned_is_exclusive": bool(owned_is_exclusive) if already_owned else False,
                "is_owned": bool(already_owned),
                "exclusive_taken": bool(exclusive_taken),
            }
        )

    return out

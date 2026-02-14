from __future__ import annotations

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.db.session import get_db
from app.models.models import Idea, IdeaStatus, User
from app.auth.deps import get_current_user

router = APIRouter(prefix="/ideas", tags=["ideas"])


@router.get("/recommended")
def recommended(
    include_owned: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(Idea).filter(Idea.status == IdeaStatus.ACTIVE)

    if not include_owned:
        q = q.filter(Idea.seller_id != current_user.id)

    ideas = (
        q.order_by(Idea.total_score.desc(), Idea.id.asc())
        .limit(50)
        .all()
    )

    # 最低限の返却（フロントで必要なら増やす）
    return [
        {
            "id": i.id,
            "title": i.title,
            "summary": i.summary,
            "price": i.price,
            "is_exclusive": i.is_exclusive,
            "status": getattr(i.status, "value", str(i.status)),
            "total_score": i.total_score,
            "seller_id": i.seller_id,
        }
        for i in ideas
    ]


# --- debug endpoints (後で消してOK) ---

@router.get("/_debug/count")
def debug_count(
    db: Session = Depends(get_db),
):
    total = db.query(Idea).count()
    active = db.query(Idea).filter(Idea.status == IdeaStatus.ACTIVE).count()
    return {"total": total, "active": active}


@router.get("/_debug/all")
def debug_all(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    rows = db.query(Idea).order_by(Idea.id.asc()).limit(limit).all()
    return [
        {
            "id": i.id,
            "title": i.title,
            "summary": i.summary,
            "price": i.price,
            "is_exclusive": i.is_exclusive,
            "status": getattr(i.status, "value", str(i.status)),
            "total_score": i.total_score,
            "seller_id": i.seller_id,
        }
        for i in rows
    ]

# --- debug helpers (safe JSON) ---
from datetime import datetime
from typing import Any

def _idea_to_public_dict(i) -> dict[str, Any]:
    # SQLAlchemy model -> JSON-serializable primitives
    def dt(x):
        if isinstance(x, datetime):
            return x.isoformat()
        return x

    return {
        "id": getattr(i, "id", None),
        "seller_id": getattr(i, "seller_id", None),
        "title": getattr(i, "title", None),
        "summary": getattr(i, "summary", None),
        "body": getattr(i, "body", None),
        "price": getattr(i, "price", None),
        "resale_allowed": getattr(i, "resale_allowed", None),
        "exclusive_option_price": getattr(i, "exclusive_option_price", None),
        "status": str(getattr(i, "status", None)),
        "total_score": getattr(i, "total_score", None),
        "created_at": dt(getattr(i, "created_at", None)),
        "updated_at": dt(getattr(i, "updated_at", None)),
    }

# NOTE: 既存 /ideas/_debug/all が壊れてても、これで中身を確認できる
@router.get("/_debug/all_json")
def debug_all_json(db: Session = Depends(get_db)):
    ideas = db.query(Idea).order_by(Idea.id.asc()).limit(200).all()
    return [_idea_to_public_dict(i) for i in ideas]


@router.get("/_debug/recommended_trace")
def debug_recommended_trace(include_owned: bool = True, db: Session = Depends(get_db)):
    """
    /ideas/recommended が 500 になる原因切り分け用（認証不要）。
    """
    try:
        rows = db.execute(text(
            "SELECT id, title, status, total_score, exclusive_option_price "
            "FROM ideas ORDER BY total_score DESC"
        )).fetchall()

        def is_active(st: str) -> bool:
            return st in ("ACTIVE", "IdeaStatus.ACTIVE")

        items = []
        for r in rows:
            st = str(r[2])
            if not is_active(st):
                continue
            items.append({
                "id": r[0],
                "title": r[1],
                "status": st,
                "total_score": float(r[3] or 0),
                "exclusive_option_price": r[4],
                "already_owned": False,
                "owned_is_exclusive": False,
                "is_owned": False,
                "exclusive_taken": False,
            })

        return {"ok": True, "count": len(items), "items": items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RECOMMENDED_TRACE_ERROR: {type(e).__name__}: {e}")


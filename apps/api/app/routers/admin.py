from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import update
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.models import Idea, UserRole
from app.auth.deps import get_current_user

router = APIRouter(prefix="/admin", tags=["admin"])


def _require_auth(payload: Dict[str, Any]) -> None:
    if not payload or payload.get("sub") is None:
        raise HTTPException(status_code=401, detail="not authenticated")


def _require_role(payload: Dict[str, Any], role: str) -> None:
    role_val = payload.get("role")
    if role_val != role:
        raise HTTPException(status_code=403, detail=f"{role.lower()}s only")


class ScoreIn(BaseModel):
    total_score: int = Field(..., ge=0, le=10_000)


class ScoreOut(BaseModel):
    ok: bool
    idea_id: int
    total_score: int


@router.post("/score/{idea_id}", response_model=ScoreOut)
def score_idea(
    idea_id: int,
    body: ScoreIn,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    total_score を更新する簡易admin API。

    MVP前提で、いったん SELLER のみ許可（必要なら ADMIN などに変更してOK）
    """
    _require_auth(current_user)
    _require_role(current_user, UserRole.SELLER.value)

    # idea が存在するかチェック
    idea = db.get(Idea, idea_id)
    if idea is None:
        raise HTTPException(status_code=404, detail="idea not found")

    # update
    db.execute(
        update(Idea).where(Idea.id == idea_id).values(total_score=int(body.total_score))
    )
    db.commit()

    # 返却用に最新を取り直す
    idea2 = db.get(Idea, idea_id)
    return ScoreOut(ok=True, idea_id=int(idea_id), total_score=int(getattr(idea2, "total_score", 0)))

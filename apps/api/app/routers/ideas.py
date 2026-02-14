from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db import get_db
from app.models import Idea
from app.auth.deps import get_current_user

router = APIRouter()

@router.get("/ideas/recommended")
def recommended(
    include_owned: bool = Query(True),
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    try:
        ideas = db.query(Idea).all()

        result = []
        for idea in ideas:
            result.append({
                "id": idea.id,
                "title": idea.title,
                "status": idea.status,
                "total_score": idea.total_score,
                "exclusive_option_price": idea.exclusive_option_price,
            })

        return result

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"RECOMMENDED_FATAL: {type(e).__name__}: {e}"
        )

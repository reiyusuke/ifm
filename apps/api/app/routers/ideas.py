from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.models import UserRole
from app.auth.deps import get_current_user

router = APIRouter(prefix="/ideas", tags=["ideas"])


def _require_auth(payload: Dict[str, Any]) -> None:
    if not payload or payload.get("sub") is None:
        raise HTTPException(status_code=401, detail="not authenticated")


def _require_role(payload: Dict[str, Any], role: str) -> None:
    role_val = payload.get("role")
    if role_val != role:
        raise HTTPException(status_code=403, detail=f"{role.lower()}s only")


def _as_bool(v: Any) -> bool:
    # sqlite の 0/1, True/False, "0"/"1" などを想定して正規化
    if isinstance(v, bool):
        return v
    if v is None:
        return False
    if isinstance(v, (int, float)):
        return bool(int(v))
    if isinstance(v, str):
        return v.strip().lower() in ("1", "true", "t", "yes", "y", "on")
    return bool(v)


def _normalize_common(d: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": int(d["id"]),
        "seller_id": int(d["seller_id"]),
        "title": d.get("title") or "",
        "summary": d.get("summary") or "",
        "body": d.get("body") or "",
        "price": float(d.get("price") or 0.0),
        "resale_allowed": _as_bool(d.get("resale_allowed")),
        "exclusive_option_price": (float(d["exclusive_option_price"]) if d.get("exclusive_option_price") is not None else None),
        "status": d.get("status"),
        "total_score": int(d.get("total_score") or 0),
    }


@router.get("/recommended")
def recommended(
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
    include_owned: bool = Query(False, description="true にすると購入済みも含めて返す"),
):
    _require_auth(current_user)
    _require_role(current_user, UserRole.BUYER.value)

    buyer_id = int(current_user["sub"])
    owned_filter = "" if include_owned else "AND d.id IS NULL"

    rows = db.execute(
        text(
            f"""
            SELECT
              i.id,
              i.seller_id,
              i.title,
              i.summary,
              i.body,
              i.price,
              i.resale_allowed,
              i.exclusive_option_price,
              i.status,
              COALESCE(i.total_score, 0) AS total_score,
              CASE WHEN d.id IS NULL THEN 0 ELSE 1 END AS already_owned
            FROM ideas i
            LEFT JOIN deals d
              ON d.idea_id = i.id
             AND d.buyer_id = :buyer_id
            WHERE i.status = 'SUBMITTED'
              {owned_filter}
            ORDER BY COALESCE(i.total_score, 0) DESC, i.id DESC
            """
        ),
        {"buyer_id": buyer_id},
    ).mappings().all()

    out: List[Dict[str, Any]] = []
    for r in rows:
        d = dict(r)
        base = _normalize_common(d)
        base["already_owned"] = _as_bool(d.get("already_owned"))
        out.append(base)
    return out


@router.get("/mine")
def mine(
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
    status: Optional[str] = Query(None, description="SUBMITTED などで絞り込み"),
):
    _require_auth(current_user)
    _require_role(current_user, UserRole.SELLER.value)

    seller_id = int(current_user["sub"])

    status_filter = ""
    params: Dict[str, Any] = {"seller_id": seller_id}
    if status:
        status_filter = "AND i.status = :status"
        params["status"] = status

    rows = db.execute(
        text(
            f"""
            SELECT
              i.id,
              i.seller_id,
              i.title,
              i.summary,
              i.body,
              i.price,
              i.resale_allowed,
              i.exclusive_option_price,
              i.status,
              COALESCE(i.total_score, 0) AS total_score
            FROM ideas i
            WHERE i.seller_id = :seller_id
              {status_filter}
            ORDER BY i.id DESC
            """
        ),
        params,
    ).mappings().all()

    out: List[Dict[str, Any]] = []
    for r in rows:
        d = dict(r)
        out.append(_normalize_common(d))
    return out

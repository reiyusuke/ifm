from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String

# Base は既存の場所から拾う（プロジェクトによって違うので2候補）
try:
    from app.db.base import Base  # type: ignore
except Exception:
    from app.db.base_class import Base  # type: ignore


class UserRole(str, enum.Enum):
    BUYER = "BUYER"
    SELLER = "SELLER"


class UserStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)

    role = Column(String, nullable=False, default=UserRole.BUYER.value)
    status = Column(String, nullable=False, default=UserStatus.ACTIVE.value)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

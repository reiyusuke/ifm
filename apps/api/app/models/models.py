from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import (
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Enum,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

# ★ ここが最重要：sessionのBaseを使う
from app.db.session import Base


# =========================
# Enums
# =========================

class UserRole(str, enum.Enum):
    BUYER = "BUYER"
    SELLER = "SELLER"
    ADMIN = "ADMIN"


class UserStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"


class IdeaStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    ARCHIVED = "ARCHIVED"


class DealStatus(str, enum.Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"


# =========================
# Models
# =========================

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True)
    password_hash: Mapped[str] = mapped_column(String)

    role: Mapped[UserRole] = mapped_column(Enum(UserRole))
    status: Mapped[UserStatus] = mapped_column(Enum(UserStatus))

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Idea(Base):
    __tablename__ = "ideas"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String)
    summary: Mapped[str] = mapped_column(String)
    body: Mapped[str] = mapped_column(String)

    seller_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    price: Mapped[float] = mapped_column(Float)
    exclusive_option_price: Mapped[float] = mapped_column(Float, nullable=True)

    resale_allowed: Mapped[bool] = mapped_column(Boolean, default=False)

    status: Mapped[IdeaStatus] = mapped_column(Enum(IdeaStatus))
    total_score: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Deal(Base):
    __tablename__ = "deals"

    id: Mapped[int] = mapped_column(primary_key=True)
    idea_id: Mapped[int] = mapped_column(ForeignKey("ideas.id"))
    buyer_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    is_exclusive: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

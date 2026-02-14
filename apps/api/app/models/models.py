from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

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
    ACTIVE = "ACTIVE"          # ★これを追加（ここが無いと落ちる）
    ARCHIVED = "ARCHIVED"


# =========================
# Models
# =========================

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)

    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False)
    status: Mapped[UserStatus] = mapped_column(Enum(UserStatus), nullable=False, default=UserStatus.ACTIVE)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    # relations
    ideas: Mapped[list["Idea"]] = relationship("Idea", back_populates="seller", cascade="all, delete-orphan")
    deals: Mapped[list["Deal"]] = relationship("Deal", back_populates="buyer", cascade="all, delete-orphan")


class Idea(Base):
    __tablename__ = "ideas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    seller_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    title: Mapped[str] = mapped_column(String, nullable=False)
    summary: Mapped[str] = mapped_column(String, nullable=False)  # ★NOT NULL 前提で埋める
    body: Mapped[str] = mapped_column(String, nullable=False)

    price: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    resale_allowed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    exclusive_option_price: Mapped[float | None] = mapped_column(Float, nullable=True)

    status: Mapped[IdeaStatus] = mapped_column(
        Enum(IdeaStatus),
        nullable=False,
        default=IdeaStatus.ACTIVE,  # ★ACTIVE 前提で動く実装があるならここで合わせる
    )

    total_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    # relations
    seller: Mapped["User"] = relationship("User", back_populates="ideas")
    deals: Mapped[list["Deal"]] = relationship("Deal", back_populates="idea", cascade="all, delete-orphan")


class Deal(Base):
    __tablename__ = "deals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    idea_id: Mapped[int] = mapped_column(Integer, ForeignKey("ideas.id"), nullable=False, index=True)
    buyer_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # ★ルータが amount=... を渡すので必須
    # 既存DBにカラムが無いケースがあるので「nullable=True」にして起動時DDLで補完する想定
    amount: Mapped[float | None] = mapped_column(Float, nullable=True)

    is_exclusive: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    # relations
    idea: Mapped["Idea"] = relationship("Idea", back_populates="deals")
    buyer: Mapped["User"] = relationship("User", back_populates="deals")

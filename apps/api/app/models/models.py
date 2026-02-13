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
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)


class Base(DeclarativeBase):
    pass


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
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


# =========================
# Models
# =========================

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole))
    status: Mapped[UserStatus] = mapped_column(Enum(UserStatus), default=UserStatus.ACTIVE)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    ideas: Mapped[list["Idea"]] = relationship(
        "Idea",
        back_populates="seller",
        cascade="all, delete",
    )

    deals: Mapped[list["Deal"]] = relationship(
        "Deal",
        back_populates="buyer",
        cascade="all, delete",
    )


class Idea(Base):
    __tablename__ = "ideas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    seller_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    title: Mapped[str] = mapped_column(String)
    summary: Mapped[str] = mapped_column(String)
    body: Mapped[str] = mapped_column(String)

    price: Mapped[float] = mapped_column(Float)
    resale_allowed: Mapped[bool] = mapped_column(Boolean, default=False)
    exclusive_option_price: Mapped[float | None] = mapped_column(Float, nullable=True)

    status: Mapped[IdeaStatus] = mapped_column(
        Enum(IdeaStatus),
        default=IdeaStatus.SUBMITTED,
    )

    # 推薦スコア（MVP用）
    total_score: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    seller: Mapped["User"] = relationship("User", back_populates="ideas")

    deals: Mapped[list["Deal"]] = relationship(
        "Deal",
        back_populates="idea",
        cascade="all, delete",
    )


class Deal(Base):
    __tablename__ = "deals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    buyer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    idea_id: Mapped[int] = mapped_column(ForeignKey("ideas.id"), index=True)

    # 購入時点の金額（後でIdeaの価格が変わっても取引は固定）
    amount: Mapped[float] = mapped_column(Float, nullable=False)

    is_exclusive: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[DealStatus] = mapped_column(Enum(DealStatus), default=DealStatus.COMPLETED)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    buyer: Mapped["User"] = relationship("User", back_populates="deals")
    idea: Mapped["Idea"] = relationship("Idea", back_populates="deals")

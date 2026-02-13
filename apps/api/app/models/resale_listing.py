from __future__ import annotations

from sqlalchemy import Column, DateTime, Float, Integer, UniqueConstraint, func

# どのBaseでも拾えるようにフォールバック（テンプレ差異吸収）
try:
    from app.db.base import Base  # type: ignore
except Exception:
    try:
        from app.db.base_class import Base  # type: ignore
    except Exception:
        from sqlalchemy.orm import declarative_base
        Base = declarative_base()  # 最悪の保険


class ResaleListing(Base):
    __tablename__ = "resale_listings"
    __table_args__ = (UniqueConstraint("idea_id", name="uq_resale_listings_idea_id"),)

    id = Column(Integer, primary_key=True, index=True)
    idea_id = Column(Integer, nullable=False, index=True)
    seller_id = Column(Integer, nullable=False, index=True)
    price = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=False), server_default=func.current_timestamp(), nullable=False)

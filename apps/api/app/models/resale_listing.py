from app.db.session import Base
from sqlalchemy import Column, Integer, DateTime, UniqueConstraint, func

class ResaleListing(Base):
    __tablename__ = "resale_listings"

    id = Column(Integer, primary_key=True, index=True)
    idea_id = Column(Integer, nullable=False, index=True)
    seller_id = Column(Integer, nullable=False, index=True)
    price = Column(Integer, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("idea_id", name="ux_resale_listings_idea_id"),
    )

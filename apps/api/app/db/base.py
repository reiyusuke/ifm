"""
Single source of truth for SQLAlchemy Base.

We re-export Base from app.db.session so other modules can do:
  from app.db.base import Base
without creating another declarative_base().
"""
from app.db.session import Base  # noqa: F401

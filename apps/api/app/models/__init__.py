"""
SQLAlchemy model registry.

ここで import されたモデルだけが Base.metadata.create_all() の対象になります。
（壊れている/非モデルのモジュールは import しない）
"""

from __future__ import annotations

# 既存の主要モデル（users / ideas / deals が入っている想定）
# ※ app/models/models.py に定義されているSQLAlchemyモデルを読み込む
from app.models.models import *  # noqa: F401,F403

# resale_listings のSQLAlchemyモデル
from app.models.resale_listing import ResaleListing  # noqa: F401

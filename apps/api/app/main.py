from __future__ import annotations

from fastapi import FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import Base, engine, SessionLocal

# ★重要: create_all 前に「全モデル」をimportしてmetadataに載せる
from app.models import models as _models  # noqa: F401
from app.models import resale_listing as _resale_listing  # noqa: F401

from app.routers import auth, ideas, deals, resale
from app.seed import seed_all

app = FastAPI()


def _ensure_deals_amount_column() -> None:
    """
    create_all は既存テーブルへのカラム追加をしない。
    なので起動時に deals.amount を DB種別に応じて追加する（存在すれば何もしない）。
    """
    url = str(engine.url)

    with engine.begin() as conn:
        # 1) まずカラム存在チェック（DB別）
        if url.startswith("sqlite"):
            cols = conn.execute(text("PRAGMA table_info(deals)")).fetchall()
            names = {r[1] for r in cols}  # r[1]=name
            if "amount" in names:
                return
            conn.execute(text("ALTER TABLE deals ADD COLUMN amount REAL"))
            return

        # Postgres / others
        # information_schema.columns で確認
        try:
            row = conn.execute(
                text(
                    """
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_name = 'deals'
                      AND column_name = 'amount'
                    LIMIT 1
                    """
                )
            ).fetchone()
            if row:
                return

            # Postgres なら DOUBLE PRECISION が無難
            conn.execute(text("ALTER TABLE deals ADD COLUMN amount DOUBLE PRECISION"))
            return
        except Exception:
            # information_schema が使えない/権限などの場合でも、失敗しても起動は継続
            # （この場合は /deals がまだ 500 になるのでログで追う）
            return


@app.on_event("startup")
def on_startup() -> None:
    # 1) テーブル作成（モデルimport済みなので全テーブル対象）
    Base.metadata.create_all(bind=engine)

    # 2) deals.amount を補完（sqlite/postgres対応）
    _ensure_deals_amount_column()

    # 3) seed（ユーザー/アイデアが無いとログインできない）
    db: Session = SessionLocal()
    try:
        seed_all(db)
    finally:
        db.close()


# ルーター登録
app.include_router(auth.router)
app.include_router(ideas.router)
app.include_router(deals.router)
app.include_router(resale.router)


@app.get("/health")
def health():
    return {"ok": True}

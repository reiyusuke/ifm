from __future__ import annotations

import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------
# Ensure "app" package is importable when running as a script in CI
# (apps/api がカレントでも確実に import できるようにする)
# ---------------------------------------------------------------------
API_ROOT = Path(__file__).resolve().parents[1]  # .../apps/api
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))


def _resolve_hash_fn():
    """
    プロジェクト内の実装差異を吸収して、パスワードハッシュ関数を1つに決める。
    """
    # まずは app.security に寄せる（いま auth.py が app.security を使っているため）
    try:
        from app.security import get_password_hash  # type: ignore

        return get_password_hash, "get_password_hash(app.security)"
    except Exception:
        pass

    # 次に app.auth.security
    try:
        from app.auth.security import get_password_hash  # type: ignore

        return get_password_hash, "get_password_hash(app.auth.security)"
    except Exception:
        pass

    # 最後の保険（非推奨）：passlib のコンテキストがあるならそれを使う
    try:
        from app.auth.security import pwd_context  # type: ignore

        return pwd_context.hash, "pwd_context.hash(app.auth.security)"
    except Exception as e:
        raise RuntimeError("No password hash function found") from e


def main() -> None:
    # DATABASE_URL は scripts/e2e.sh 側で export 済みの想定
    db_url = os.getenv("DATABASE_URL", "")
    if not db_url:
        raise RuntimeError("DATABASE_URL is not set")

    # -----------------------------------------------------------------
    # ここが重要：モデルを必ず import してから create_all する
    # （これをしないと metadata に users/ideas/deals 等が乗らずテーブルが作られない）
    # -----------------------------------------------------------------
    # 可能性のあるモデル集約モジュールを全部試す（存在するものだけ読み込む）
    try:
        import app.models.models  # noqa: F401
    except Exception:
        pass
    try:
        import app.models.user  # noqa: F401
    except Exception:
        pass
    try:
        import app.models.idea  # noqa: F401
    except Exception:
        pass
    try:
        import app.models.score  # noqa: F401
    except Exception:
        pass

    # engine / Base を取得（プロジェクト構成の差異を吸収）
    try:
        from app.db.session import engine  # type: ignore
    except Exception as e:
        raise RuntimeError("cannot import engine from app.db.session") from e

    Base = None
    try:
        from app.db.base import Base as _Base  # type: ignore

        Base = _Base
    except Exception:
        pass

    if Base is None:
        # fallback: session.py などに Base がある構成
        try:
            from app.db.session import Base as _Base  # type: ignore

            Base = _Base
        except Exception as e:
            raise RuntimeError("cannot import Base (app.db.base or app.db.session)") from e

    # create schema
    Base.metadata.create_all(bind=engine)

    # seed users
    from sqlalchemy import select
    from sqlalchemy.orm import Session

    from app.models.models import User, UserRole  # type: ignore

    hash_fn, hash_name = _resolve_hash_fn()

    BUYER_EMAIL = os.getenv("E2E_BUYER_EMAIL", "realbuyer@ifm.com").strip().lower()
    BUYER_PASS = os.getenv("E2E_BUYER_PASS", "password").strip()

    SELLER_EMAIL = os.getenv("E2E_SELLER_EMAIL", "realseller@ifm.com").strip().lower()
    SELLER_PASS = os.getenv("E2E_SELLER_PASS", "password").strip()

    def ensure_user(db: Session, email: str, password: str, role_val: str) -> None:
        u = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
        if u:
            return
        db.add(
            User(
                email=email,
                password_hash=hash_fn(password),
                role=role_val,
                status="ACTIVE",
            )
        )
        db.commit()

    with Session(engine) as db:
        ensure_user(db, BUYER_EMAIL, BUYER_PASS, UserRole.BUYER.value)
        ensure_user(db, SELLER_EMAIL, SELLER_PASS, UserRole.SELLER.value)

    print(f"USING_HASH_FN = {hash_name}")
    print("OK: schema created & users seeded")


if __name__ == "__main__":
    main()

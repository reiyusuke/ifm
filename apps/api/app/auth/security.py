from __future__ import annotations

# Keep backward compatibility for modules importing app.auth.security.*
# Internally delegate everything to app.security (single source of truth).

from app.security import (  # noqa: F401
    ACCESS_TOKEN_MINUTES,
    ALGORITHM,
    SECRET_KEY,
    create_access_token,
    decode_access_token,
    get_password_hash,
    verify_password,
)

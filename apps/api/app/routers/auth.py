# （中略：既存importはそのまま）

# ログイン部分だけ修正版例
@router.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        raise HTTPException(status_code=401, detail="invalid credentials")

    if not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="invalid credentials")

    try:
        token = create_access_token(
            user_id=user.id,
            role=user.role.value,   # ★ FIX
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TOKEN_ERROR: {e}")

    return {"access_token": token, "token_type": "bearer"}

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.models import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    RefreshRequest,
    CurrentUser,
)
from backend.auth.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_refresh_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from backend.database import get_db
from backend.auth.deps import get_current_user   # 下一步会创建

router = APIRouter(prefix="/auth", tags=["认证"])

# ── 注册 ─────────────────────────────────────────────────
@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    # 1. 检查用户名是否已存在
    row = await db.execute(
        text("SELECT id FROM users WHERE username = :username"),
        {"username": body.username},
    )
    if row.fetchone():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="用户名已存在",
        )

    # 2. ✅ 检查是否是第一个用户，是则设为 admin
    count_row = await db.execute(text("SELECT COUNT(*) FROM users"))
    user_count = count_row.scalar()  # 取出数量
    role = "admin" if user_count == 0 else "user"

    # 3. 插入新用户（带 role 字段）
    await db.execute(
        text("""
            INSERT INTO users (username, hashed_password, phone, email, gender, role)
            VALUES (:username, :hashed_password, :phone, :email, :gender, :role)
        """),
        {
            "username":        body.username,
            "hashed_password": hash_password(body.password),
            "phone":           body.phone,
            "email":           body.email,
            "gender":          body.gender,
            "role":            role,        # ✅ 新增
        },
    )
    await db.commit()

    return {"message": "注册成功"}

# ── 登录 ─────────────────────────────────────────────────
@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    # 1. 查用户
    row = await db.execute(
        text("SELECT id, username, hashed_password, role, is_active FROM users WHERE username = :username"),
        {"username": body.username},
    )
    user = row.fetchone()

    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账号已被禁用",
        )

    # 2. 生成 token
    access_token  = create_access_token(user.id, user.username, user.role)
    refresh_token = create_refresh_token(user.id)

    # 3. 存 refresh_token 哈希到数据库
    expires_at = datetime.now(timezone.utc).replace(tzinfo=None)
    await db.execute(
        text("""
            INSERT INTO refresh_tokens (user_id, token_hash, expires_at)
            VALUES (:user_id, :token_hash, NOW() + INTERVAL '7 days')
        """),
        {
            "user_id":    user.id,
            "token_hash": hash_refresh_token(refresh_token),
        },
    )
    await db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

# ── 刷新 Token ───────────────────────────────────────────
@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    body: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    # 1. 解码校验
    payload = decode_token(body.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="refresh token 无效或已过期",
        )

    user_id = int(payload["sub"])

    # 2. 校验数据库中是否存在且未撤销
    token_hash = hash_refresh_token(body.refresh_token)
    row = await db.execute(
        text("""
            SELECT id FROM refresh_tokens
            WHERE user_id = :user_id
              AND token_hash = :token_hash
              AND revoked = FALSE
              AND expires_at > NOW()
        """),
        {"user_id": user_id, "token_hash": token_hash},
    )
    if not row.fetchone():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="refresh token 已失效，请重新登录",
        )

    # 3. 查用户信息
    row = await db.execute(
        text("SELECT id, username, role, is_active FROM users WHERE id = :id"),
        {"id": user_id},
    )
    user = row.fetchone()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账号不可用",
        )

    # 4. 旧 token 撤销 + 签发新 token（rotation 机制）
    await db.execute(
        text("UPDATE refresh_tokens SET revoked = TRUE WHERE user_id = :user_id AND token_hash = :token_hash"),
        {"user_id": user_id, "token_hash": token_hash},
    )

    new_access  = create_access_token(user.id, user.username, user.role)
    new_refresh = create_refresh_token(user.id)

    await db.execute(
        text("""
            INSERT INTO refresh_tokens (user_id, token_hash, expires_at)
            VALUES (:user_id, :token_hash, NOW() + INTERVAL '7 days')
        """),
        {
            "user_id":    user.id,
            "token_hash": hash_refresh_token(new_refresh),
        },
    )
    await db.commit()

    return TokenResponse(
        access_token=new_access,
        refresh_token=new_refresh,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

# ── 登出 ─────────────────────────────────────────────────
@router.post("/logout")
async def logout(
    body: RefreshRequest,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    # 撤销该 refresh token
    await db.execute(
        text("""
            UPDATE refresh_tokens
            SET revoked = TRUE
            WHERE user_id = :user_id
              AND token_hash = :token_hash
        """),
        {
            "user_id":    current_user.id,
            "token_hash": hash_refresh_token(body.refresh_token),
        },
    )
    await db.commit()
    return {"message": "已登出"}

# ── 获取当前用户信息 ──────────────────────────────────────
@router.get("/me", response_model=CurrentUser)
async def me(current_user: CurrentUser = Depends(get_current_user)):
    return current_user

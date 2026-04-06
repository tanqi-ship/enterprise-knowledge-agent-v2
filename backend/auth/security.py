from datetime import datetime, timedelta, timezone
from typing import Optional
import hashlib

import bcrypt
from jose import JWTError, jwt

from backend.config import config

# ── 密码哈希（直接使用 bcrypt，绕过 passlib 兼容问题）────────────────────────
def hash_password(plain: str) -> str:
    """对密码进行 bcrypt 哈希，自动截断超过 72 字节的密码"""
    password_bytes = plain.encode("utf-8")[:72]
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password_bytes, salt).decode("utf-8")

def verify_password(plain: str, hashed: str) -> bool:
    """验证明文密码与哈希是否匹配"""
    password_bytes = plain.encode("utf-8")[:72]
    return bcrypt.checkpw(password_bytes, hashed.encode("utf-8"))

# ── JWT 配置 ─────────────────────────────────────────────────────────────────
ACCESS_TOKEN_EXPIRE_MINUTES = 15      # access token 15 分钟
REFRESH_TOKEN_EXPIRE_DAYS   = 7       # refresh token 7 天
ALGORITHM                   = "HS256"

def _get_secret() -> str:
    """从 config 读取 JWT_SECRET，缺失时直接报错"""
    secret = getattr(config, "JWT_SECRET", None)
    if not secret:
        raise RuntimeError("JWT_SECRET 未配置，请在 .env 中添加")
    return secret

# ── Access Token ──────────────────────────────────────────────────────────────
def create_access_token(user_id: int, username: str, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub":      str(user_id),
        "username": username,
        "role":     role,
        "exp":      expire,
        "type":     "access",
    }
    return jwt.encode(payload, _get_secret(), algorithm=ALGORITHM)

# ── Refresh Token ─────────────────────────────────────────────────────────────
def create_refresh_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub":  str(user_id),
        "exp":  expire,
        "type": "refresh",
    }
    return jwt.encode(payload, _get_secret(), algorithm=ALGORITHM)

# ── 解码（两种 token 通用）────────────────────────────────────────────────────
def decode_token(token: str) -> Optional[dict]:
    """
    成功返回 payload dict，
    失败（过期 / 签名错误 / 格式错误）返回 None
    """
    try:
        return jwt.decode(token, _get_secret(), algorithms=[ALGORITHM])
    except JWTError:
        return None

# ── Refresh Token 存库用的哈希（不存明文）─────────────────────────────────────
def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()

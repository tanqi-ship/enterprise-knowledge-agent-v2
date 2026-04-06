from pydantic import BaseModel, field_validator
from typing import Optional

# ── 注册 ────────────────────────────────────────────────
class RegisterRequest(BaseModel):
    username: str
    password: str
    phone:    Optional[str] = None
    email:    Optional[str] = None
    gender:   Optional[str] = None

    @field_validator("username")
    @classmethod
    def username_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("用户名不能为空")
        if len(v) < 2 or len(v) > 50:
            raise ValueError("用户名长度须在 2~50 个字符之间")
        return v

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("密码长度不能少于 6 位")
        return v

    @field_validator("phone")
    @classmethod
    def phone_format(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if v and not v.isdigit():
            raise ValueError("手机号只能包含数字")
        return v or None

# ── 登录 ────────────────────────────────────────────────
class LoginRequest(BaseModel):
    username: str
    password: str

# ── Token 响应 ──────────────────────────────────────────
class TokenResponse(BaseModel):
    access_token:  str
    refresh_token: str
    token_type:    str = "bearer"
    expires_in:    int      # access token 有效秒数

# ── 刷新 ────────────────────────────────────────────────
class RefreshRequest(BaseModel):
    refresh_token: str

# ── 当前用户信息（注入到路由） ───────────────────────────
class CurrentUser(BaseModel):
    id:       int
    username: str
    role:     str
    is_active: bool

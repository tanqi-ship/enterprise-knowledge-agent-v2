from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from backend.auth.models import CurrentUser
from backend.auth.security import decode_token

# ── Bearer Token 提取器 ───────────────────────────────────
# auto_error=True：没有 Authorization 头时自动返回 403
bearer_scheme = HTTPBearer(auto_error=True)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> CurrentUser:
    """
    从 Authorization: Bearer <token> 中解析出当前用户。
    任何异常统一返回 401。
    """
    token = credentials.credentials

    # 1. 解码
    payload = decode_token(token)

    # 2. 基础校验
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="token 无效或已过期",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. 必须是 access token
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="请使用 access token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 4. 提取字段
    user_id  = payload.get("sub")
    username = payload.get("username")
    role     = payload.get("role")

    if not all([user_id, username, role]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="token 载荷不完整",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 5. 构造并返回 CurrentUser
    return CurrentUser(
        id=int(user_id),
        username=username,
        role=role,
        is_active=True,   # 能通过 decode 说明 token 本身有效
    )

# ── 角色守卫（可选，按需在路由中使用） ────────────────────
def require_role(*roles: str):
    """
    用法：
        @router.get("/admin", dependencies=[Depends(require_role("admin"))])
    或者：
        current_user: CurrentUser = Depends(require_role("admin", "superadmin"))
    """
    async def _checker(
        current_user: CurrentUser = Depends(get_current_user),
    ) -> CurrentUser:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"权限不足，需要角色：{' / '.join(roles)}",
            )
        return current_user

    return _checker

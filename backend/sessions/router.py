import time
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from langchain_core.messages import AIMessage, HumanMessage

from backend.database import get_db
from backend.sessions.service import (
    db_list_sessions,
    db_create_session,
    db_update_title,
    db_delete_session,
)
from backend.auth.deps import get_current_user
from backend.auth.models import CurrentUser

router = APIRouter(prefix="/sessions", tags=["会话"])

class TitleRequest(BaseModel):
    title: str

# ── 获取所有会话 ──────────────────────────────────────────
@router.get("")
async def get_sessions(
    current_user: CurrentUser = Depends(get_current_user),  # 添加当前用户依赖
    session: AsyncSession = Depends(get_db)  # ✅ 注入 session
):
    """获取所有会话列表"""
    return await db_list_sessions(session,current_user.id)

# ── 新建会话 ──────────────────────────────────────────────
@router.post("")
async def new_session(
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)  # ✅ 注入 session
):
    """新建会话"""
    thread_id = f"thread_{int(time.time())}"
    return await db_create_session(session, thread_id,current_user.id)

# ── 获取某个会话的历史消息 ────────────────────────────────
@router.get("/{thread_id}")
async def get_session_messages(
        thread_id: str,
        current_user: CurrentUser = Depends(get_current_user)
):
    """获取某个会话的历史消息"""
    from backend.agent import build_graph
    agent = build_graph()

    config_dict = {"configurable": {"thread_id": thread_id}}
    state = agent.get_state(config_dict)

    if not state or not state.values:
        return {"messages": []}

    result = []
    for msg in state.values.get("messages", []):
        if isinstance(msg, HumanMessage):
            result.append({"role": "user", "content": msg.content})
        elif isinstance(msg, AIMessage) and not msg.tool_calls and msg.content:
            result.append({"role": "assistant", "content": msg.content})

    return {"messages": result}

# ── 修改会话标题 ──────────────────────────────────────────
@router.put("/{thread_id}/title")
async def update_title(                          # ✅ 改为 async def
    thread_id: str,
    req: TitleRequest,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)      # ✅ 注入 session
):
    """修改会话标题"""
    await db_update_title(session, thread_id, req.title)  # ✅ 加 await
    return {"success": True}

# ── 删除会话 ──────────────────────────────────────────────
@router.delete("/{thread_id}")
async def delete_session(                        # ✅ 改为 async def
    thread_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)      # ✅ 注入 session
):
    """删除会话"""
    await db_delete_session(session, thread_id)  # ✅ 加 await
    return {"success": True}

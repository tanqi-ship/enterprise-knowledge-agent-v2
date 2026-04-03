import time
from fastapi import APIRouter
from pydantic import BaseModel
from langchain_core.messages import AIMessage, HumanMessage
from backend.sessions.service import (
    db_list_sessions, db_create_session,
    db_update_title, db_delete_session
)

router = APIRouter(prefix="/sessions", tags=["会话"])


class TitleRequest(BaseModel):
    title: str


@router.get("")
def get_sessions():
    """获取所有会话列表"""
    return db_list_sessions()


@router.post("")
def new_session():
    """新建会话"""
    thread_id = f"thread_{int(time.time())}"
    return db_create_session(thread_id)


@router.get("/{thread_id}")
def get_session_messages(thread_id: str):
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


@router.put("/{thread_id}/title")
def update_title(thread_id: str, req: TitleRequest):
    """修改会话标题"""
    db_update_title(thread_id, req.title)
    return {"success": True}


@router.delete("/{thread_id}")
def delete_session(thread_id: str):
    """删除会话"""
    db_delete_session(thread_id)
    return {"success": True}

from fastapi import APIRouter,Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from backend.sessions.service import db_update_title, db_update_time
from backend.agent import build_graph
from backend.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
import json

router = APIRouter(prefix="/sessions", tags=["聊天"])

agent = build_graph()


class ChatRequest(BaseModel):
    message: str


@router.post("/{thread_id}/chat")
def chat(thread_id: str, req: ChatRequest,db: AsyncSession = Depends(get_db)):
    """发送消息，返回完整回答（非流式）"""
    config_dict = {"configurable": {"thread_id": thread_id}}
    input_state = {"messages": [HumanMessage(content=req.message)]}

    final_answer = ""
    for chunk, metadata in agent.stream(input_state, config_dict, stream_mode="messages"):
        if isinstance(chunk, AIMessage) and not chunk.tool_calls and chunk.content:
            final_answer += chunk.content

    # 第一条消息自动设为标题
    state = agent.get_state(config_dict)
    messages = state.values.get("messages", [])
    if len(messages) == 2:
        title = req.message[:20] + ("..." if len(req.message) > 20 else "")
        db_update_title(thread_id, title,)

    db_update_time(thread_id)
    return {"answer": final_answer, "thread_id": thread_id}


@router.post("/{thread_id}/chat/stream")
def chat_stream(thread_id: str, req: ChatRequest,db: AsyncSession = Depends(get_db)):
    """发送消息，流式返回（打字机效果）"""
    config_dict = {"configurable": {"thread_id": thread_id}}
    input_state = {"messages": [HumanMessage(content=req.message)]}

    async def generate():
        for chunk, metadata in agent.stream(input_state, config_dict, stream_mode="messages"):
            if isinstance(chunk, AIMessage) and chunk.tool_calls:
                for tc in chunk.tool_calls:
                    yield f"data: {json.dumps({'type': 'tool', 'name': tc['name']}, ensure_ascii=False)}\n\n"

            elif isinstance(chunk, ToolMessage):
                yield f"data: {json.dumps({'type': 'tool_result', 'content': chunk.content[:50]}, ensure_ascii=False)}\n\n"

            elif isinstance(chunk, AIMessage) and not chunk.tool_calls and chunk.content:
                yield f"data: {json.dumps({'type': 'text', 'content': chunk.content}, ensure_ascii=False)}\n\n"

        # 更新标题和时间
        state = agent.get_state(config_dict)
        messages = state.values.get("messages", [])
        if len(messages) == 2:
            title = req.message[:20] + ("..." if len(req.message) > 20 else "")
            await db_update_title(db,thread_id, title)
        await db_update_time(db,thread_id)

        yield f"data: {json.dumps({'type': 'done'}, ensure_ascii=False)}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")

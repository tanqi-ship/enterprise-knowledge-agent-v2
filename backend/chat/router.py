from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from backend.sessions.service import db_update_title, db_update_time
from backend.agent import build_graph

router = APIRouter(prefix="/sessions", tags=["聊天"])

agent = build_graph()


class ChatRequest(BaseModel):
    message: str


@router.post("/{thread_id}/chat")
def chat(thread_id: str, req: ChatRequest):
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
        db_update_title(thread_id, title)

    db_update_time(thread_id)
    return {"answer": final_answer, "thread_id": thread_id}


@router.post("/{thread_id}/chat/stream")
def chat_stream(thread_id: str, req: ChatRequest):
    """发送消息，流式返回（打字机效果）"""
    config_dict = {"configurable": {"thread_id": thread_id}}
    input_state = {"messages": [HumanMessage(content=req.message)]}

    def generate():
        for chunk, metadata in agent.stream(input_state, config_dict, stream_mode="messages"):
            if isinstance(chunk, AIMessage) and chunk.tool_calls:
                for tc in chunk.tool_calls:
                    yield f"data: {{'type':'tool','name':'{tc['name']}'}}\n\n"

            elif isinstance(chunk, ToolMessage):
                yield f"data: {{'type':'tool_result','content':'{chunk.content[:50]}'}}\n\n"

            elif isinstance(chunk, AIMessage) and not chunk.tool_calls and chunk.content:
                content = chunk.content.replace('"', '\\"').replace('\n', '\\n')
                yield f"data: {{'type':'text','content':'{content}'}}\n\n"

        # 更新标题和时间
        state = agent.get_state(config_dict)
        messages = state.values.get("messages", [])
        if len(messages) == 2:
            title = req.message[:20] + ("..." if len(req.message) > 20 else "")
            db_update_title(thread_id, title)
        db_update_time(thread_id)

        yield "data: {'type':'done'}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")

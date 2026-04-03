import httpx
from langchain_core.messages import AIMessage, SystemMessage,HumanMessage,ToolMessage,RemoveMessage
from langchain_core.runnables import Runnable
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import ToolNode

from config import config
from .state import AgentState
from .tools import all_tools


def _build_llm() -> Runnable:
    llm = ChatOpenAI(
        model=config.QWEN_MODEL,
        temperature=config.TEMPERATURE,
        api_key=config.QWEN_API_KEY,
        base_url=config.QWEN_BASE_URL,
        http_client=httpx.Client(
            proxy=config.PROXY,  # 有代理走代理，None 则直连
            timeout=60,
        ),
    )
    return llm.bind_tools(all_tools)


llm: Runnable = _build_llm()


def _summarize_messages(messages: list) -> str:
    """把早期对话压缩成一段摘要"""
    history_text = ""
    for msg in messages:
        if isinstance(msg, HumanMessage):
            history_text += f"用户：{msg.content}\n"
        elif isinstance(msg, AIMessage) and msg.content:
            history_text += f"助手：{msg.content}\n"
        elif isinstance(msg, ToolMessage):
            history_text += f"工具结果：{msg.content}\n"

    summary_prompt = f"""
请将以下对话历史压缩成一段简洁的摘要，必须保留：
1. 用户询问过的具体问题（城市名、地点等关键词）
2. 工具查询到的具体数据（天气数据、计算结果等）
3. 重要的上下文信息

{history_text}

摘要：
"""
    # 注意：这里用不带 tools 的纯 llm 来生成摘要
    # 避免摘要过程中又触发工具调用
    pure_llm = ChatOpenAI(
        model=config.QWEN_MODEL,
        temperature=0,  # 摘要用0温度，保证稳定
        api_key=config.QWEN_API_KEY,
        base_url=config.QWEN_BASE_URL,
        http_client=httpx.Client(
            proxy=config.PROXY,
            timeout=60,
        ),
    )
    response = pure_llm.invoke([HumanMessage(content=summary_prompt)])
    return response.content


def agent_node(state: AgentState) -> AgentState:
    """核心决策节点：调用 LLM，决定直接回答或调用工具"""
    all_messages = state["messages"]

    # 判断当前 iteration 是否是新一轮对话的开始
    # 新一轮对话：最后一条消息是 HumanMessage
    from langchain_core.messages import HumanMessage as HM
    last_msg = all_messages[-1]
    if isinstance(last_msg, HM):
        # 新一轮对话开始，重置迭代次数
        current_iteration = 1
    else:
        # 工具调用返回后继续，累加迭代次数
        current_iteration = state.get("iteration", 0) + 1

    if len(all_messages) > config.SUMMARY_THRESHOLD:
        old_messages = all_messages[:-20]
        recent_messages = all_messages[-20:]

        print(f"\n📝 历史消息过长（{len(all_messages)}条），正在压缩早期对话...")
        summary = _summarize_messages(old_messages)
        print(f"✅ 压缩完成,已删除 {len(old_messages)} 条早期消息")

        system_message = SystemMessage(
            content=(
                f"{config.SYSTEM_PROMPT}\n\n"
                f"以下是早期对话的摘要，供你参考：\n{summary}"
            )
        )
        messages_to_remove = [RemoveMessage(id=m.id) for m in old_messages]

        # 本次 LLM 调用用的消息
        messages_for_llm = [system_message] + recent_messages
        response: AIMessage = llm.invoke(messages_for_llm)
        return {
            # 先删除旧消息，再追加新回答
            # add_messages 会先处理 RemoveMessage，再追加新消息
            "messages": messages_to_remove + [response],
            "iteration": current_iteration,
        }


    else:
        system_message = SystemMessage(content=config.SYSTEM_PROMPT)
        messages = [system_message] + all_messages
        response: AIMessage = llm.invoke(messages)

    return {
        "messages": [response],
        "iteration": current_iteration,  # ← 用重置后的值
    }



tool_node = ToolNode(all_tools)

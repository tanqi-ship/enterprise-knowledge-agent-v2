import httpx
from langchain_core.messages import AIMessage, SystemMessage,HumanMessage,ToolMessage,RemoveMessage
from langchain_core.runnables import Runnable
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import ToolNode
import logging
from backend.config import config
from .state import AgentState
from .tools import all_tools
import time

logger = logging.getLogger(__name__)

def _build_llm() -> Runnable:
    logger.info(f"初始化 LLM: {config.QWEN_MODEL}")  # 记录 LLM 初始化
    llm = ChatOpenAI(
        model=config.QWEN_MODEL,
        temperature=config.TEMPERATURE,
        api_key=config.QWEN_API_KEY,
        base_url=config.QWEN_BASE_URL,
        http_client=httpx.Client(
            # proxy=config.PROXY,  # 有代理走代理，None 则直连
            timeout=60,
        ),
    )
    logger.debug("LLM初始化成功，正在绑定工具...")
    return llm.bind_tools(all_tools)


llm: Runnable = _build_llm()


def _summarize_messages(messages: list) -> str:
    """把早期对话压缩成一段摘要"""
    logger.info(f"开始摘要早期对话消息 {len(messages)} 条.")  # 记录开始
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
    logger.debug("调用纯LLM进行摘要...")
    pure_llm = ChatOpenAI(
        model=config.QWEN_MODEL,
        temperature=0,  # 摘要用0温度，保证稳定
        api_key=config.QWEN_API_KEY,
        base_url=config.QWEN_BASE_URL,
        http_client=httpx.Client(
            # proxy=config.PROXY,
            timeout=60,
        ),
    )
    response = pure_llm.invoke([HumanMessage(content=summary_prompt)])
    logger.info("消息摘要完成.")
    return response.content


def agent_node(state: AgentState) -> AgentState:
    start = time.time()
    """核心决策节点：调用 LLM，决定直接回答或调用工具"""
    logger.info("进入节点 agent_node.")  # 记录进入节点
    all_messages = state["messages"]
    logger.debug(f"状态包含 {len(all_messages)} 条消息.")

    # 判断当前 iteration 是否是新一轮对话的开始
    # 新一轮对话：最后一条消息是 HumanMessage
    from langchain_core.messages import HumanMessage as HM

    today = datetime.now().strftime("%Y年%m月%d日")
    system_content = config.SYSTEM_PROMPT.replace("{today}", today)  # ← 第二处：生成带日期的提示词

    
    last_msg = all_messages[-1]
    if isinstance(last_msg, HM):
        # 新一轮对话开始，重置迭代次数
        current_iteration = 1
        logger.info("检测到新的对话轮次，正在重置迭代计数.")
    else:
        # 工具调用返回后继续，累加迭代次数
        current_iteration = state.get("iteration", 0) + 1
        logger.info(f"持续对话, iteration: {current_iteration}")

    if len(all_messages) > config.SUMMARY_THRESHOLD:
        old_messages = all_messages[:-20]
        recent_messages = all_messages[-20:]

        logger.warning(f"\n📝 历史消息过长（{len(all_messages)}条），正在压缩早期对话...")
        summary = _summarize_messages(old_messages)
        logger.info("摘要已创建，正在为LLM准备消息...")
        print(f"✅ 压缩完成,已删除 {len(old_messages)} 条早期消息")

        system_message = SystemMessage(
            content=(
                f"{system_content}\n\n"
                f"以下是早期对话的摘要，供你参考：\n{summary}"
            )
        )
        messages_to_remove = [RemoveMessage(id=m.id) for m in old_messages]

        # 本次 LLM 调用用的消息
        messages_for_llm = [system_message] + recent_messages
        logger.debug("使用总结的上下文调用LLM...")  # 记录 LLM 调用前
        response: AIMessage = llm.invoke(messages_for_llm)
        logger.info(
            f"LLM responded. Tool calls: {bool(response.tool_calls)}, Content length: {len(response.content) if response.content else 0}")  # 记录 LLM 调用后

        print("\n--- DEBUG: LLM Response ---")
        print(f"Content: {response.content}")
        print(f"Tool Calls: {response.tool_calls}")
        print("--- END DEBUG ---\n")

        # 记录具体的工具调用或回复内容
        if response.tool_calls:
            logger.info(f"LLM decided to call tools: {[tc['name'] for tc in response.tool_calls]}")
        else:
            logger.info(f"LLM decided to respond directly: {response.content[:50]}...") # 只记录前50个字符


        return {
            # 先删除旧消息，再追加新回答
            # add_messages 会先处理 RemoveMessage，再追加新消息
            "messages": messages_to_remove + [response],
            "iteration": current_iteration,
        }


    else:
        system_message = SystemMessage(content=system_content)
        messages = [system_message] + all_messages
        logger.debug("Invoking LLM with full context...")  # 记录 LLM 调用前
        response: AIMessage = llm.invoke(messages)
        print(f"⏱️ LLM 推理耗时：{time.time() - start:.2f}s")

        logger.info(
            f"LLM responded. Tool calls: {bool(response.tool_calls)}, Content length: {len(response.content) if response.content else 0}")  # 记录 LLM 调用后

        if response.tool_calls:
            logger.info(f"LLM decided to call tools: {[tc['name'] for tc in response.tool_calls]}")
        else:
            logger.info(f"LLM decided to respond directly: {response.content[:50]}...") # 只记录前50个字符


    return {
        "messages": [response],
        "iteration": current_iteration,  # ← 用重置后的值
    }



tool_node = ToolNode(all_tools)

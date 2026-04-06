from langchain_core.messages import AIMessage
from langgraph.graph import END

from backend.config import config
from .state import AgentState


def should_continue(state: AgentState) -> str:
    """
    路由逻辑：
      - 超过最大迭代次数 → END
      - LLM 返回工具调用  → "tools"
      - 其他              → END
    """
    last_message = state["messages"][-1]
    iteration = state.get("iteration", 0)

    if iteration >= config.MAX_ITERATIONS:
        print(f"⚠️  已达到最大迭代次数（{config.MAX_ITERATIONS}），强制结束")
        return END

    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "tools"

    return END

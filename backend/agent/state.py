from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]  # 消息列表，自动追加
    iteration: int                            # 当前迭代次数

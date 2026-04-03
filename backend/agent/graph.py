import sqlite3
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import START, END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from .edges import should_continue
from .nodes import agent_node, tool_node
from .state import AgentState

DB_PATH = "memory.db"

# ← 在模块级别创建连接，保持连接不关闭
_conn = sqlite3.connect(DB_PATH, check_same_thread=False)
_db = SqliteSaver(_conn)


def build_graph() -> CompiledStateGraph:
    graph = StateGraph(AgentState)

    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)

    graph.add_edge(START, "agent")
    graph.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            END: END,
        },
    )
    graph.add_edge("tools", "agent")

    return graph.compile(checkpointer=_db)

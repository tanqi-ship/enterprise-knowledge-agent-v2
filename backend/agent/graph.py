from langgraph.checkpoint.postgres import PostgresSaver
from psycopg_pool import ConnectionPool          # ✅ 使用连接池
from langgraph.graph import START, END, StateGraph
from langgraph.graph.state import CompiledStateGraph
from backend.config import config
from .edges import should_continue
from .nodes import agent_node, tool_node
from .state import AgentState

# ✅ 连接池：自动管理连接的创建/回收/重连
_pool = ConnectionPool(
    conninfo=config.CHECKPOINT_DB_URL,
    min_size=1,
    max_size=10,
    open=True,           # 立即建立连接
)
_db = PostgresSaver(_pool)
_db.setup()

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

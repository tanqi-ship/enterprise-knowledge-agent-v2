from langgraph.checkpoint.postgres import PostgresSaver
from psycopg_pool import ConnectionPool          # ✅ 使用连接池
from langgraph.graph import START, END, StateGraph
from langgraph.graph.state import CompiledStateGraph
from backend.config import config
from .edges import should_continue
from .nodes import agent_node, tool_node
from .state import AgentState

import psycopg

# # ✅ 连接池：自动管理连接的创建/回收/重连
# _pool = ConnectionPool(
#     conninfo=config.CHECKPOINT_DB_URL,
#     min_size=1,
#     max_size=10,
#     open=True,           # 立即建立连接
# )
# _db = PostgresSaver(_pool)
# _db.setup()

# 第一步：用 autocommit 独立连接做初始化
with psycopg.connect(config.CHECKPOINT_DB_URL, autocommit=True) as setup_conn:
    PostgresSaver(setup_conn).setup()

# 第二步：业务用连接池（normal 事务模式）
_pool = ConnectionPool(
    conninfo=config.CHECKPOINT_DB_URL,
    min_size=1,
    max_size=10,
)
_db = PostgresSaver(_pool)

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

import time
import sqlite3
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.checkpoint.sqlite import SqliteSaver

from backend.agent import build_graph

# 全局 app
conn = sqlite3.connect("memory.db", check_same_thread=False)
checkpointer = SqliteSaver(conn)
app = build_graph()


def run_turn(user_input: str, thread_id: str) -> str:
    print(f"\n🧑 用户：{user_input}")

    config_dict = {"configurable": {"thread_id": thread_id}}
    input_state = {"messages": [HumanMessage(content=user_input)]}

    final_answer = ""
    is_first_chunk = True
    printed_tool_calls = False

    for chunk, metadata in app.stream(
        input_state,
        config_dict,
        stream_mode="messages"
    ):
        # 工具结果到达时，从 state 里读完整的工具调用参数
        if isinstance(chunk, ToolMessage):
            if not printed_tool_calls:
                state = app.get_state(config_dict)
                messages = state.values.get("messages", [])
                for msg in reversed(messages):
                    if isinstance(msg, AIMessage) and msg.tool_calls:
                        for tc in msg.tool_calls:
                            print(f"\n🔧 调用工具：{tc['name']}")
                            print(f"   参数：{tc['args']}")
                        break
                printed_tool_calls = True

            # ✅ 找到对应工具名再打印结果
            state = app.get_state(config_dict)
            messages = state.values.get("messages", [])
            for msg in reversed(messages):
                if isinstance(msg, AIMessage) and msg.tool_calls:
                    for tc in msg.tool_calls:
                        if tc["id"] == chunk.tool_call_id:
                            print(f"   ↳ [{tc['name']}] 结果：{chunk.content}")
                    break

            is_first_chunk = True


        # AI 流式输出
        elif isinstance(chunk, AIMessage) and not chunk.tool_calls and chunk.content:
            printed_tool_calls = False  # 重置，准备下一轮工具调用
            if is_first_chunk:
                print(f"\n🤖 助手：", end="", flush=True)
                is_first_chunk = False
            print(chunk.content, end="", flush=True)
            final_answer += chunk.content

    print()
    db_update_time(thread_id)
    return final_answer


def list_sessions() -> list[str]:
    """查看数据库中所有会话"""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT DISTINCT thread_id, MAX(checkpoint_id) "
        "FROM checkpoints GROUP BY thread_id "
        "ORDER BY MAX(checkpoint_id) DESC"
    )
    return cursor.fetchall()


def delete_session(thread_id: str):
    """删除会话及其所有历史消息"""
    cursor = conn.cursor()

    # 查一下这三张表实际存在哪些
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    )
    tables = [row[0] for row in cursor.fetchall()]
    print(f"当前数据库表：{tables}")

    # 删除所有相关表里该 thread_id 的数据
    for table in ["checkpoints", "checkpoint_blobs", "checkpoint_writes"]:
        if table in tables:
            cursor.execute(
                f"DELETE FROM {table} WHERE thread_id = ?",
                (thread_id,)
            )

    conn.commit()
    print(f"🗑️  已删除会话：{thread_id}")


def show_history(thread_id: str):
    """查看某个会话的历史"""
    config_dict = {"configurable": {"thread_id": thread_id}}
    state = app.get_state(config_dict)

    if not state or not state.values:
        print(f"❌ 没有找到会话 [{thread_id}] 的记录")
        return

    messages = state.values.get("messages", [])
    print(f"\n📝 会话 [{thread_id}] 共 {len(messages)} 条消息：")
    print("=" * 50)

    for msg in messages:
        if isinstance(msg, HumanMessage):
            print(f"\n🧑 用户：{msg.content}")
        elif isinstance(msg, AIMessage):
            if msg.tool_calls:
                for tc in msg.tool_calls:
                    print(f"\n🔧 工具：{tc['name']} {tc['args']}")
            elif msg.content:
                print(f"\n🤖 助手：{msg.content}")
        elif isinstance(msg, ToolMessage):
            print(f"   ↳ {msg.content[:80]}...")

def db_create_session(thread_id: str):
    """新建会话时同步写入 sessions 表"""
    from datetime import datetime
    now = datetime.now().isoformat()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            thread_id   TEXT PRIMARY KEY,
            title       TEXT DEFAULT '新对话',
            created_at  TEXT,
            updated_at  TEXT
        )
    """)
    conn.execute(
        "INSERT OR IGNORE INTO sessions (thread_id, title, created_at, updated_at) "
        "VALUES (?, ?, ?, ?)",
        (thread_id, "新对话", now, now)
    )
    conn.commit()


def db_update_time(thread_id: str):
    """更新会话最后活跃时间"""
    from datetime import datetime
    conn.execute(
        "UPDATE sessions SET updated_at = ? WHERE thread_id = ?",
        (datetime.now().isoformat(), thread_id)
    )
    conn.commit()


def list_sessions() -> list[str]:
    """查看数据库中所有会话"""
    cursor = conn.cursor()

    # 确保表存在
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            thread_id   TEXT PRIMARY KEY,
            title       TEXT DEFAULT '新对话',
            created_at  TEXT,
            updated_at  TEXT
        )
    """)

    # ✅ 改成从 sessions 表查
    cursor.execute(
        "SELECT thread_id, title, updated_at "
        "FROM sessions ORDER BY updated_at DESC"
    )
    return cursor.fetchall()


def chat_loop():
    """交互式多轮对话"""

    # 启动时先展示历史会话，让用户选择
    sessions = list_sessions()

    if sessions:
        print(f"\n{'=' * 50}")
        print(f"📋 历史会话（共 {len(sessions)} 个）：")
        for i, (tid, title, updated_at) in enumerate(sessions):
            print(f"  [{i + 1}] {tid} - {title}")
        print(f"{'=' * 50}")
        print("💡 输入数字继续历史会话，直接回车开始新会话")

        choice = input("请选择：").strip()

        if choice.isdigit() and 1 <= int(choice) <= len(sessions):
            # 继续历史会话
            current_thread = sessions[int(choice) - 1][0]
            print(f"\n🔄 继续会话：{current_thread}")
            show_history(current_thread)
        else:
            # 新会话
            current_thread = f"thread_{int(time.time())}"
            db_create_session(current_thread)
            print(f"\n🆕 新会话开始（会话ID：{current_thread}）")
    else:
        # 没有历史记录，直接新建
        current_thread = f"thread_{int(time.time())}"
        print(f"\n🚀 新会话开始（会话ID：{current_thread}）")

    print(f"{'=' * 50}")
    print("💡 指令：")
    print("   new              → 开始新会话")
    print("   sessions         → 查看所有历史会话")
    print("   switch <id>      → 切换到某个历史会话")
    print("   history          → 查看当前会话历史")
    print("   delete <id>     → 删除某个会话")
    print("   exit             → 退出")
    print(f"{'=' * 50}")

    while True:
        try:
            user_input = input("\n🧑 你：").strip()
        except KeyboardInterrupt:
            print("\n👋 再见！")
            break

        if not user_input:
            continue

        if user_input.lower() == "exit":
            print("👋 再见！")
            break

        if user_input.lower() == "new":
            current_thread = f"thread_{int(time.time())}"
            print(f"🆕 新会话开始（会话ID：{current_thread}）")
            continue

        if user_input.lower() == "sessions":
            sessions = list_sessions()
            if not sessions:
                print("📭 暂无历史会话")
            else:
                print(f"\n📋 所有历史会话（共 {len(sessions)} 个）：")
                for i, (tid, _) in enumerate(sessions):
                    flag = " ← 当前" if tid == current_thread else ""
                    print(f"  [{i + 1}] {tid}{flag}")
            continue


        if user_input.lower().startswith("switch "):
            target = user_input[7:].strip()
            sessions = list_sessions()
            thread_ids = [s[0] for s in sessions]
            if target in thread_ids:
                current_thread = target
                print(f"🔄 已切换到会话：{current_thread}")
                show_history(current_thread)
            else:
                print(f"❌ 找不到会话：{target}")
            continue

        if user_input.lower() == "history":
            show_history(current_thread)
            continue

        if user_input.lower().startswith("delete "):
            target = user_input[7:].strip()
            sessions = list_sessions()
            thread_ids = [s[0] for s in sessions]

            if target not in thread_ids:
                print(f"❌ 找不到会话：{target}")
                continue

            # 如果删的是当前会话，新建一个
            if target == current_thread:
                delete_session(target)
                current_thread = f"thread_{int(time.time())}"
                print(f"🆕 已删除当前会话，新会话开始：{current_thread}")
            else:
                delete_session(target)

            continue

        run_turn(user_input, current_thread)



def main():
    chat_loop()


if __name__ == "__main__":
    main()

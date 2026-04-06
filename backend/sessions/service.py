from datetime import datetime, timezone
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# ── 查询所有会话 ──────────────────────────────────────────
async def db_list_sessions(session: AsyncSession, user_id: int) -> list[dict]:
    result = await session.execute(
        text("""
            SELECT thread_id, title, created_at, updated_at
            FROM sessions
            WHERE user_id = :user_id
            ORDER BY updated_at DESC
        """),
        {"user_id": user_id}
    )
    rows = result.fetchall()
    return [
        {
            "thread_id": row[0],
            "title":     row[1],
            "created_at": row[2],
            "updated_at": row[3],
        }
        for row in rows
    ]

# ── 创建会话 ──────────────────────────────────────────────
async def db_create_session(
    session: AsyncSession,
    thread_id: str,
    user_id: int,
    title: str = "新对话"
) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    await session.execute(
        text("""
            INSERT INTO sessions (thread_id, user_id, title, created_at, updated_at)
            VALUES (:thread_id, :user_id, :title, :created_at, :updated_at)
        """),
        {
            "thread_id":  thread_id,
            "user_id":    user_id,
            "title":      title,
            "created_at": now,
            "updated_at": now,
        }
    )
    await session.commit()
    return {"thread_id": thread_id, "title": title, "created_at": now}

# ── 更新标题 ──────────────────────────────────────────────
async def db_update_title(
    session: AsyncSession,
    thread_id: str,
    title: str
) -> None:
    now = datetime.now(timezone.utc).isoformat()
    await session.execute(
        text("""
            UPDATE sessions
            SET title = :title, updated_at = :updated_at
            WHERE thread_id = :thread_id
        """),
        {"title": title, "updated_at": now, "thread_id": thread_id}
    )
    await session.commit()

# ── 更新时间戳 ────────────────────────────────────────────
async def db_update_time(
    session: AsyncSession,
    thread_id: str
) -> None:
    now = datetime.now(timezone.utc).isoformat()
    await session.execute(
        text("""
            UPDATE sessions
            SET updated_at = :updated_at
            WHERE thread_id = :thread_id
        """),
        {"updated_at": now, "thread_id": thread_id}
    )
    await session.commit()

# ── 删除会话 ──────────────────────────────────────────────
async def db_delete_session(
    session: AsyncSession,
    thread_id: str
) -> None:
    await session.execute(
        text("DELETE FROM sessions WHERE thread_id = :thread_id"),
        {"thread_id": thread_id}
    )
    await session.commit()

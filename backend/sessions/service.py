from datetime import datetime
from backend.database import conn


def db_list_sessions() -> list[dict]:
    cursor = conn.cursor()
    cursor.execute(
        "SELECT thread_id, title, created_at, updated_at "
        "FROM sessions ORDER BY updated_at DESC"
    )
    rows = cursor.fetchall()
    return [
        {
            "thread_id": row[0],
            "title": row[1],
            "created_at": row[2],
            "updated_at": row[3],
        }
        for row in rows
    ]


def db_create_session(thread_id: str) -> dict:
    now = datetime.now().isoformat()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO sessions (thread_id, title, created_at, updated_at) "
        "VALUES (?, ?, ?, ?)",
        (thread_id, "新对话", now, now)
    )
    conn.commit()
    return {"thread_id": thread_id, "title": "新对话", "created_at": now}


def db_update_title(thread_id: str, title: str):
    conn.execute(
        "UPDATE sessions SET title = ?, updated_at = ? WHERE thread_id = ?",
        (title, datetime.now().isoformat(), thread_id)
    )
    conn.commit()


def db_update_time(thread_id: str):
    conn.execute(
        "UPDATE sessions SET updated_at = ? WHERE thread_id = ?",
        (datetime.now().isoformat(), thread_id)
    )
    conn.commit()


def db_delete_session(thread_id: str):
    conn.execute("DELETE FROM sessions WHERE thread_id = ?", (thread_id,))
    conn.commit()

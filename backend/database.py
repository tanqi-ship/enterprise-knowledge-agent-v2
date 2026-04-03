import sqlite3

conn = sqlite3.connect("memory.db", check_same_thread=False)

def init_db():
    """启动时自动建表"""
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            thread_id   TEXT PRIMARY KEY,
            title       TEXT DEFAULT '新对话',
            created_at  TEXT,
            updated_at  TEXT
        )
    """)
    conn.commit()

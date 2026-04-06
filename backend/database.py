from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text
from backend.config import config

# ── 引擎（连接池） ────────────────────────────────────────
# DATABASE_URL 格式须为：
#   postgresql+asyncpg://user:password@host:port/dbname
engine = create_async_engine(
    config.DATABASE_URL,
    echo=False,       # True 时会打印所有 SQL，调试用
    pool_size=10,
    max_overflow=20,
)

# ── Session 工厂 ──────────────────────────────────────────
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)

# ── FastAPI 依赖注入 ───────────────────────────────────────
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise

# ── 启动时建表 ────────────────────────────────────────────
async def init_db():
    async with engine.begin() as conn:

        # ── 用户表 ────────────────────────────────────────
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id            SERIAL PRIMARY KEY,
                username      VARCHAR(50)  UNIQUE NOT NULL,
                phone         VARCHAR(20)  UNIQUE,
                email         VARCHAR(100) UNIQUE,
                gender        VARCHAR(10),
                hashed_password TEXT         NOT NULL,
                role          VARCHAR(20)  NOT NULL DEFAULT 'user',
                is_active     BOOLEAN      NOT NULL DEFAULT TRUE,
                created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
                updated_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
            )
        """))

        # ── 会话表 ────────────────────────────────────────
        await conn.execute(text("DROP TABLE IF EXISTS sessions CASCADE"))
        await conn.execute(text("""
            CREATE TABLE sessions (
                thread_id  TEXT    PRIMARY KEY,
                user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                title      TEXT    NOT NULL DEFAULT '新对话',
                created_at TEXT    NOT NULL,
                updated_at TEXT    NOT NULL
            )
        """))

        # ── Refresh Token 表 ──────────────────────────────
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS refresh_tokens (
                id         SERIAL  PRIMARY KEY,
                user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                token_hash TEXT    NOT NULL,
                revoked    BOOLEAN NOT NULL DEFAULT FALSE,
                expires_at TIMESTAMPTZ NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """))

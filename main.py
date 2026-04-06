from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.database import init_db
from backend.rag import ensure_collection
from backend.sessions.router import router as sessions_router
from backend.chat.router import router as chat_router
from backend.documents.router import router as documents_router
from backend.analyze.router import router as analyze_router
from backend.auth.router import router as auth_router
from backend.agent.graph import _pool,build_graph
from backend.logging_config import setup_logging
import logging

"""
# 启动 FastAPI 后端
uvicorn main:app --reload --port 8000
"""

# ─── 生命周期（替代原来顶层直接调用） ──────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    ensure_collection()
    yield                  # 启动完成
    _pool.close()          # ✅ 服务关闭时释放所有连接


# --- 在应用启动前配置日志 ---
setup_logging(log_level=logging.INFO)
# ─── 应用 ─────────────────────────────────────────
app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── 注册路由 ──────────────────────────────────────
app.include_router(sessions_router)
app.include_router(chat_router)
app.include_router(documents_router)
app.include_router(analyze_router)
app.include_router(auth_router)

@app.get("/")
async def root():
    return {"message": "服务正常运行"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

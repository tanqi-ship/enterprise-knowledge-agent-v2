from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.database import init_db
from backend.rag import ensure_collection
from backend.sessions.router import router as sessions_router
from backend.chat.router import router as chat_router
from backend.documents.router import router as documents_router
from backend.analyze.router import router as analyze_router
"""
# 启动 FastAPI 后端
uvicorn main:app --reload --port 8000
"""

# ─── 初始化 ───────────────────────────────────────
init_db()           # 自动建表
ensure_collection() # 确保 Qdrant collection 存在

# ─── 应用 ─────────────────────────────────────────
app = FastAPI()

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


@app.get("/")
def root():
    return {"message": "服务正常运行"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)



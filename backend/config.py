import os
from dotenv import load_dotenv

load_dotenv()


class Config:

    # LLM
    QWEN_API_KEY: str = os.getenv("QWEN_API_KEY", "")
    QWEN_BASE_URL: str = os.getenv("QWEN_BASE_URL", "https://api.siliconflow.cn/v1")
    QWEN_MODEL: str = os.getenv("QWEN_MODEL", "Qwen/Qwen3.5-9B")
    # 温度
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0"))
    # 最大推理数
    MAX_ITERATIONS: int = int(os.getenv("MAX_ITERATIONS", "10"))
    # 代理地址
    PROXY: str | None = os.getenv("PROXY",None)
    SYSTEM_PROMPT: str = (
        "你是一个智能助手，可以使用工具帮助用户解决问题。\n"
        "回答用户问题时，必须优先调用 rag_search 工具搜索知识库，\n"  
        "再结合检索结果给出准确回答。\n"
        "只有当知识库中没有相关内容时，才使用自身知识回答。\n"  
        "如果 rag_search 没有找到相关信息，或者问题涉及实时、公共信息（如新闻、天气、股价、网络热点等），"
        "则调用 web_search 工具进行搜索，注意将用户原始问题的关键信息作为 'query' 参数传给 web_search。\n"
        "请根据 web_search 的结果进行回答。\n"
        "用户问关于天气的情况，如：怎么样，如何等，需要根据天气进行建议，比如穿衣建议，出行建议等\n"
        "如果不需要工具，请直接给出简洁准确的回答。"
    )

    # 最大摘要数
    SUMMARY_THRESHOLD: int = int(os.getenv("SUMMARY_THRESHOLD", "60"))

    # ── Qdrant ────────────────────────────────────────
    QDRANT_HOST: str = os.getenv("QDRANT_HOST", "localhost")
    QDRANT_PORT: int = int(os.getenv("QDRANT_PORT", "6333"))
    QDRANT_COLLECTION: str = os.getenv("QDRANT_COLLECTION", "company_docs")

    # ── SiliconFlow Embedding ─────────────────────────
    EMBEDDING_API_KEY: str = os.getenv("EMBEDDING_API_KEY", "")
    EMBEDDING_BASE_URL: str = os.getenv("EMBEDDING_BASE_URL", "https://api.siliconflow.cn/v1")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")
    EMBEDDING_DIM: int = 1024  # bge-m3 输出维度固定是 1024

    # 重排序模型
    RERANKER_BASE_URL: str = os.getenv("RERANKER_BASE_URL", "")
    RERANKER_API_KEY: str = os.getenv("RERANKER_API_KEY", "")
    RERANKER_MODEL: str = os.getenv("RERANKER_MODEL", "")

    BOCHA_API_KEY: str = os.getenv("BOCHA_API_KEY", "")
    BOCHA_BASE_URL: str = os.getenv("BOCHA_BASE_URL", "")

    # PostgreSQL
    # POSTGRES_USER = os.getenv("POSTGRES_USER", "your_username")
    # POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "your_password")
    # POSTGRES_DB = os.getenv("POSTGRES_DB", "your_database_name")
    # POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
    # POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")

    # 业务数据库连接 URL（psycopg2 同步驱动）
    DATABASE_URL = os.getenv("DATABASE_URL", "")

    # LangGraph Checkpoint 专用 URL（psycopg 同步驱动）
    CHECKPOINT_DB_URL = os.getenv("CHECKPOINT_DB_URL", "")

    JWT_SECRET: str = os.getenv("JWT_SECRET", "")


config = Config()

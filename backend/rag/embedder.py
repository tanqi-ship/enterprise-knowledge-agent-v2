# rag/embedder.py
# 调用 SiliconFlow Embedding API，把文本转成向量

import httpx
from backend.config import config


def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    把一批文本转成向量
    texts: ["文本1", "文本2", ...]
    返回: [[0.1, 0.2, ...], [0.3, 0.4, ...]]
    """
    with httpx.Client(timeout=60) as client:
        response = client.post(
            f"{config.EMBEDDING_BASE_URL}/embeddings",
            headers={
                "Authorization": f"Bearer {config.EMBEDDING_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": config.EMBEDDING_MODEL,
                "input": texts,
                "encoding_format": "float",
            },
        )
        response.raise_for_status()
        data = response.json()

    # SiliconFlow 返回格式：
    # {"data": [{"index": 0, "embedding": [...]}, ...]}
    embeddings = sorted(data["data"], key=lambda x: x["index"])
    return [item["embedding"] for item in embeddings]


def embed_query(text: str) -> list[float]:
    """
    把单条查询文本转成向量
    用于检索时把用户问题向量化
    """
    return embed_texts([text])[0]

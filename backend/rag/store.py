# rag/store.py
# Qdrant 的存取操作

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams,
    PointStruct, Filter, FieldCondition, MatchValue
)
from config import config


def _get_client() -> QdrantClient:
    # return QdrantClient(
    #     host=config.QDRANT_HOST,
    #     port=config.QDRANT_PORT,
    # )
    # 直接保存到项目目录
    return QdrantClient(path="./qdrant_data")


def ensure_collection():
    """
    确保 collection 存在
    不存在则自动创建
    程序启动时调用一次
    """
    client = _get_client()
    existing = [c.name for c in client.get_collections().collections]

    if config.QDRANT_COLLECTION not in existing:
        client.create_collection(
            collection_name=config.QDRANT_COLLECTION,
            vectors_config=VectorParams(
                size=config.EMBEDDING_DIM,
                distance=Distance.COSINE,  # 余弦相似度
            ),
        )
        print(f"✅ 已创建 Qdrant collection: {config.QDRANT_COLLECTION}")
    else:
        print(f"✅ Qdrant collection 已存在: {config.QDRANT_COLLECTION}")


def save_chunks(chunks: list, embeddings: list[list[float]]):
    """
    把文本块和对应的向量存入 Qdrant
    chunks:     TextChunk 列表
    embeddings: 对应的向量列表
    """
    client = _get_client()

    points = [
        PointStruct(
            id=abs(hash(f"{chunk.source}_{chunk.chunk_index}")) % (2 ** 63),
            vector=embedding,
            payload={
                "content": chunk.content,
                "source": chunk.source,
                "chunk_index": chunk.chunk_index,
            },
        )
        for chunk, embedding in zip(chunks, embeddings)
    ]

    client.upsert(
        collection_name=config.QDRANT_COLLECTION,
        points=points,
    )


def search_similar(query_vector: list[float], top_k: int = 5) -> list[dict]:
    """
    用向量检索最相似的文本块
    返回：[{"content": "...", "source": "...", "score": 0.9}, ...]
    """
    client = _get_client()

    # results = client.search(
    #     collection_name=config.QDRANT_COLLECTION,
    #     query_vector=query_vector,
    #     limit=top_k,
    #     with_payload=True,
    # )
    results = client.query_points(
        collection_name=config.QDRANT_COLLECTION,
        query=query_vector,
        limit=top_k,
        with_payload=True,
    ).points

    return [
        {
            "content": hit.payload["content"],
            "source": hit.payload["source"],
            "score": round(hit.score, 4),
        }
        for hit in results
    ]


def delete_by_source(source: str):
    """
    删除某个文件的所有文本块
    用于重新上传文件时先清除旧数据
    """
    client = _get_client()
    client.delete(
        collection_name=config.QDRANT_COLLECTION,
        points_selector=Filter(
            must=[
                FieldCondition(
                    key="source",
                    match=MatchValue(value=source),
                )
            ]
        ),
    )

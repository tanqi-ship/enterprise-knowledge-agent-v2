# rag/ingest.py
# 入口：上传文件 → 切割 → 向量化 → 存入 Qdrant

import os
from backend.rag.loader import load_file
from backend.rag.embedder import embed_texts
from backend.rag.store import save_chunks, delete_by_source


def ingest_file(file_path: str) -> dict:
    """
    处理单个文件
    返回处理结果
    """
    filename = os.path.basename(file_path)
    print(f"\n📄 开始处理文件：{filename}")

    # 1. 读取并切割文件
    chunks = load_file(file_path)
    print(f"   切割完成：共 {len(chunks)} 个文本块")

    if not chunks:
        return {"file": filename, "status": "empty", "chunks": 0}

    # 2. 先删除该文件的旧数据（支持重新上传覆盖）
    delete_by_source(filename)

    # 3. 批量向量化（每批最多 32 条，避免超过 API 限制）
    all_embeddings = []
    batch_size = 32

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i: i + batch_size]
        texts = [chunk.content for chunk in batch]
        embeddings = embed_texts(texts)
        all_embeddings.extend(embeddings)
        print(f"   向量化进度：{min(i + batch_size, len(chunks))}/{len(chunks)}")

    # 4. 存入 Qdrant
    save_chunks(chunks, all_embeddings)
    print(f"✅ 文件处理完成：{filename}，已存入 {len(chunks)} 个文本块")

    return {
        "file": filename,
        "status": "success",
        "chunks": len(chunks),
    }

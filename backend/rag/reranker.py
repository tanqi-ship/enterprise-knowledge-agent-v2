import requests
from backend.config import config


def rerank(query: str, results: list[dict], top_k: int = 5,threshold: float = 0.5) -> list[dict]:
    """
    调用硅基流动重排序 API，对初检结果重新排序

    Args:
        query:   用户问题
        results: search_similar() 返回的结果列表
        top_k:   重排后取前几个
        threshold: 相关度阈值，低于此分数的结果直接丢弃

    Returns:
        重排后的结果列表
    """
    if not results:
        return []

    # 提取文本内容，传给重排序 API
    documents = [r["content"] for r in results]

    try:
        response = requests.post(
            url=config.RERANKER_BASE_URL,
            headers={
                "Authorization": f"Bearer {config.RERANKER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": config.RERANKER_MODEL,
                "query": query,
                "documents": documents,
                "top_n": top_k,  # 返回前 top_k 个
                "return_documents": False,  # 不用返回文档内容，我们自己有
            },
            timeout=10
        )


        response.raise_for_status()
        data = response.json()

        # 按重排序结果重新组装
        # data["results"] 格式：[{"index": 原始索引, "relevance_score": 分数}, ...]
        reranked = []
        for item in data["results"]:
            # ✅ 低于阈值直接丢弃
            if item["relevance_score"] < threshold:
                print(f"⚠️ 片段相关度过低({item['relevance_score']:.4f})，已过滤")
                continue
            original = results[item["index"]]  # 根据原始索引取回完整数据
            reranked.append({
                "content": original["content"],
                "source": original["source"],
                "score": round(item["relevance_score"], 4),  # 替换为重排序分数
            })

            # ✅ 过滤后如果没有结果，返回空列表
            if not reranked:
                print("⚠️ 所有片段相关度均低于阈值，无有效结果")
                return []

        return reranked

    except Exception as e:
        # 重排序失败，降级返回原始结果的前 top_k 个
        print(f"⚠️ 重排序失败，使用原始结果：{e}")
        return results[:top_k]

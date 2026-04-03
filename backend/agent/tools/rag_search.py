# agent/tools/rag_search.py
# RAG 检索工具，只返回检索结果，由 LLM 负责最终回答

from langchain_core.tools import tool
from backend.rag.embedder import embed_query
from backend.rag.store import search_similar
from backend.rag.reranker import rerank


@tool
def rag_search(query: str) -> str:
    """
    在知识库文档中检索与问题相关的内容。
    当用户询问任何问题时，优先使用此工具搜索知识库，
    再结合检索结果回答用户问题。
    """
    try:
        # 1. 把问题转成向量
        query_vector = embed_query(query)

        # 2. 检索最相似的文本块
        results = search_similar(query_vector, top_k=20)

        if not results:
            return "未在公司文档中找到相关内容。"

        # 3. 重排序：从 20 个里精选 5 个
        reranked = rerank(query, results, top_k=5)

        # 4. 格式化返回结果给 LLM
        output = "以下是从公司文档中检索到的相关内容：\n\n"
        if not reranked:
            return "未在知识库中找到与问题相关的内容。"

        for i, result in enumerate(reranked, 1):
            output += f"【片段{i}】来源：{result['source']}（相似度：{result['score']}）\n"
            output += f"{result['content']}\n\n"

        return output

    except Exception as e:
        return f"文档检索失败：{str(e)}"

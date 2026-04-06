import os
import httpx
from langchain_core.tools import tool
from dotenv import load_dotenv

load_dotenv()

BOCHA_API_KEY = os.getenv("BOCHA_API_KEY", "")
BOCHA_BASE_URL = os.getenv("BOCHA_BASE_URL", "https://api.bochaai.com/v1/web-search")


def _fetch_search_results(query: str, count: int = 5, freshness: str = "noLimit") -> list[dict] | None:
    """
    调用博查 API 执行网络搜索

    :param query: 搜索关键词
    :param count: 返回结果数量（建议 1-10）
    :param freshness: 时效过滤，可选 noLimit / day / week / month
    :return: 搜索结果列表 或 None
    """
    url = f"{BOCHA_BASE_URL}/v1/web-search"
    headers = {
        "Authorization": f"Bearer {BOCHA_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "query": query,
        "count": count,
        "freshness": freshness,
        "summary": True,  # 返回 AI 摘要
    }
    try:
        response = httpx.post(url, json=payload, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()

        # 博查返回结构：data.webPages.value
        web_pages = (
            data.get("data", {})
            .get("webPages", {})
            .get("value", [])
        )
        return web_pages if web_pages else None

    except Exception:
        return None


def _format_search_results(query: str, results: list[dict]) -> str:
    """格式化搜索结果为可读文本"""
    lines = [f"【{query}的搜索结果】\n"]
    for idx, item in enumerate(results, start=1):
        title = item.get("name", "无标题")
        url = item.get("url", "")
        snippet = item.get("snippet", "暂无摘要")
        lines.append(
            f"{idx}. {title}\n"
            f"   摘要：{snippet}\n"
            f"   来源：{url}\n"
        )
    return "\n".join(lines)


@tool
def search_web(query: str) -> str:
    """
    使用博查（Bocha）搜索引擎在互联网上检索实时信息。
    适用于需要最新资讯、新闻、产品信息、技术文档等场景。
    直接传入自然语言问题或关键词即可。
    例如：'2025年春节档票房冠军'、'Python 3.13 新特性'。
    """
    # 第一步：调用博查 API 获取搜索结果
    results = _fetch_search_results(query)
    if not results:
        return f"未找到关于「{query}」的搜索结果，请换个关键词后重试"

    # 第二步：格式化返回
    return _format_search_results(query, results)

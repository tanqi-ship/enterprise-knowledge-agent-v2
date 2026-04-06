import os
import httpx
from langchain_core.tools import tool
from dotenv import load_dotenv
from backend.config import config
import json


# 定义 freshness 的有效选项，用于验证输入
FRESHNESS_OPTIONS = ["day", "week", "month", "quarter", "halfYear", "year", "any"]


def _perform_web_search(
        query: str,
        count: int = 3,
        freshness: str = "any",
        summary: bool = True
) -> dict | None:  # 注意：返回值可能包含 results 和 summary
    """
    执行博查 Web 搜索
    返回包含搜索结果和摘要的字典 或 None
    """
    url = config.BOCHA_BASE_URL  # 使用官方 URL
    headers = {
        "Authorization": f"Bearer {config.BOCHA_API_KEY}",
        "Content-Type": "application/json"
    }
    # 验证 freshness 参数
    if freshness not in FRESHNESS_OPTIONS:
        print(f"[Web Search Warning] Invalid freshness value: {freshness}. Using 'any'.")
        freshness = "any"

    payload = {
        "query": query,
        "count": count,  # 使用 count 替代 num_results
        "freshness": freshness,  # 添加 freshness 参数
        "summary": summary  # 添加 summary 参数
    }

    try:
        response = httpx.post(url, headers=headers, json=payload, timeout=15)
        response.raise_for_status()
        data = response.json()

        # 检查 API 返回状态 (官方样例未明确说明状态码字段，但通常 200 OK 表示成功)
        if response.status_code == 200:
            return data  # 直接返回整个响应体，包含 results 和可能的 summary

        print(f"[Web Search Error] API returned status {response.status_code}, body: {data}")
        return None

    except httpx.TimeoutException:
        print("[Web Search Error] 请求超时")
        return None
    except httpx.HTTPStatusError as e:
        print(f"[Web Search Error] HTTP 错误 {e.response.status_code}: {e.response.text}")
        return None
    except Exception as e:
        print(f"[Web Search Error] 请求失败: {str(e)}")
        return None


def _format_search_results(data: dict) -> str:
    """
    格式化搜索结果和摘要为可读文本
    """
    output_parts = []

    # 如果有 AI 摘要，则优先展示
    if data.get("summary"):
        output_parts.append(f"【AI 搜索摘要】\n{data['summary']}\n")

    # 展示详细结果
    if data.get("results"):
        output_parts.append("【详细搜索结果】")
        for i, item in enumerate(data["results"], 1):
            title = item.get("title", "无标题")
            url = item.get("url", "无链接")
            snippet = item.get("snippet", "无摘要")

            output_parts.append(
                f"\n{i}. 【{title}】\n"
                f"   链接：{url}\n"
                f"   摘要：{snippet}"
            )
    else:
        output_parts.append("\n未找到相关搜索结果。")

    return "\n".join(output_parts)


@tool
def web_search(
        query: str,
        count: int = 3,
        freshness: str = "any",
        summary: bool = True
) -> str:
    """
    使用博查（Bocha）搜索引擎在互联网上检索实时信息。
    适用于需要最新资讯、新闻、产品信息、技术文档等场景。
    直接传入自然语言问题或关键词即可。
    例如：'2025年春节档票房冠军'、'Python 3.13 新特性'。

    Args:
        query (str): 用户希望搜索的具体问题或关键词。必须是完整的句子或短语。
                     例如：如果用户问 "北京今天天气怎么样？"，则 query 应为 "北京今天天气怎么样？"。
                     如果用户说 "帮我查一下"，则 query 应为 "帮我查一下" 后面跟着的具体内容。
        count (int, optional): 返回结果数量，默认为 3 条
        freshness (str, optional): 搜索结果的时效性，可选 "day", "week", "month",
                                  "quarter", "halfYear", "year", "any"。默认为 "any"。
        summary (bool, optional): 是否生成 AI 摘要，默认为 True。

    Returns:
        str: 包含 AI 摘要（如果有）和/或详细搜索结果的格式化文本
    """
    # 第一步：执行搜索
    raw_data = _perform_web_search(query, count, freshness, summary)

    if not raw_data:
        return f"未能获取关于「{query}」的搜索结果，请稍后重试或更换关键词。"

    # 第二步：格式化结果
    formatted_output = _format_search_results(raw_data)

    return formatted_output
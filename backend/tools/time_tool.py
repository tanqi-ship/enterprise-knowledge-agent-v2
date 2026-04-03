from datetime import datetime
from langchain_core.tools import tool


@tool
def get_current_time() -> str:
    """获取当前系统时间"""
    now = datetime.now()
    return f"当前时间：{now.strftime('%Y-%m-%d %H:%M:%S')}"

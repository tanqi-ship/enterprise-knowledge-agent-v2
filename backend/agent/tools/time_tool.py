from datetime import datetime
from langchain_core.tools import tool


@tool
def get_current_time(timezone: str = "Asia/Chongqing") -> str:
    """获取当前系统时间,timezone 参数可选，默认为 Asia/Chongqing"""
    now = datetime.now()
    return f"当前时间：{now.strftime('%Y-%m-%d %H:%M:%S')}"

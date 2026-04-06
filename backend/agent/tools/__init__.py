from .calculate import calculate
from .weather import search_weather
from .time_tool import get_current_time
from .rag_search import rag_search
from .web_search import web_search


# 统一导出，新增工具只需在此注册
all_tools = [
    calculate,
    search_weather,
    get_current_time,
    rag_search,
    web_search,
]

__all__ = ["all_tools"]

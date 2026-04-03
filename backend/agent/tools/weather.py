import os
import httpx
from langchain_core.tools import tool
from dotenv import load_dotenv

load_dotenv()

QWEATHER_API_KEY = os.getenv("QWEATHER_API", "")
QWEATHER_API_HOST = os.getenv("QWEATHER_API_HOST", "")


def _lookup_location_id(city: str) -> tuple[str, str] | None:
    """
    通过城市名查询 LocationID
    返回 (location_id, 城市标准名) 或 None
    """
    url = f"https://{QWEATHER_API_HOST}/geo/v2/city/lookup"
    params = {
        "location": city,
        "key": QWEATHER_API_KEY,
        "lang": "zh",  # 返回中文
    }
    try:
        response = httpx.get(url, params=params, timeout=10)
        data = response.json()

        if data.get("code") == "200" and data.get("location"):
            first = data["location"][0]  # 取第一个匹配结果
            return first["id"], first["name"]

        return None

    except Exception:
        return None


def _fetch_weather(location_id: str) -> dict | None:
    """通过 LocationID 查询实时天气"""
    url = f"https://{QWEATHER_API_HOST}/v7/weather/now"
    params = {
        "location": location_id,
        "key": QWEATHER_API_KEY,
        "lang": "zh",
    }
    try:
        response = httpx.get(url, params=params, timeout=10)
        data = response.json()

        if data.get("code") == "200":
            return data.get("now")

        return None

    except Exception:
        return None


def _format_weather(city: str, now: dict) -> str:
    """格式化天气数据为可读文本"""
    return (
        f"【{city}实时天气】\n"
        f"  天气状况：{now.get('text', 'N/A')}\n"
        f"  温度：{now.get('temp', 'N/A')}°C"
        f"（体感 {now.get('feelsLike', 'N/A')}°C）\n"
        f"  湿度：{now.get('humidity', 'N/A')}%\n"
        f"  风向：{now.get('windDir', 'N/A')}"
        f" {now.get('windScale', 'N/A')}级\n"
        f"  能见度：{now.get('vis', 'N/A')} km\n"
        f"  气压：{now.get('pressure', 'N/A')} hPa\n"
        f"  降水量：{now.get('precip', 'N/A')} mm"
    )


@tool
def search_weather(city: str) -> str:
    """
    查询指定城市的实时天气信息。
    支持国内外任意城市，直接传入城市名即可。
    例如：北京、上海、纽约、tokyo、london。
    """
    # 第一步：城市名 → LocationID
    result = _lookup_location_id(city)
    if not result:
        return f"未找到「{city}」，请检查城市名是否正确"

    location_id, city_name = result

    # 第二步：LocationID → 实时天气
    now = _fetch_weather(location_id)
    if not now:
        return f"获取「{city_name}」天气失败，请稍后重试"

    # 第三步：格式化返回
    return _format_weather(city_name, now)

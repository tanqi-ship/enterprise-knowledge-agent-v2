from langchain_core.tools import tool


@tool
def calculate(expression: str) -> str:
    """计算数学表达式，例如：'2 + 3 * 4'"""
    try:
        result = eval(expression, {"__builtins__": {}}, {})
        return f"计算结果：{expression} = {result}"
    except Exception as e:
        return f"计算错误：{str(e)}"

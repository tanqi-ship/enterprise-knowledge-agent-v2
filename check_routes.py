# check_routes.py
import sys
import os

# 如果你的 main.py 在子文件夹里，需要调整路径，比如 sys.path.append("app")
# 这里假设 main.py 就在当前目录
from main import app

print("当前后端所有生效的路由：")
for route in app.routes:
    # 打印所有路径，包括方法
    if hasattr(route, "path") and hasattr(route, "methods"):
        print(f"{list(route.methods)} \t {route.path}")
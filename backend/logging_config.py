# backend/logging_config.py

import logging
import os
from datetime import datetime

def setup_logging(log_level=logging.INFO):
    """
    配置项目的日志记录器。

    Args:
        log_level: 日志级别，默认为 INFO。
    """
    # --- 1. 定义日志格式 ---
    # %(asctime)s: 时间戳
    # %(levelname)s: 日志级别 (INFO, DEBUG, ERROR, etc.)
    # %(name)s: 记录器名称 (e.g., __main__, my_module)
    # %(message)s: 日志消息内容
    # %(funcName)s: 记录日志的函数名
    # %(lineno)d: 记录日志的行号
    log_format = (
        "%(asctime)s [%(levelname)-5s] [%(name)s:%(funcName)s:%(lineno)d] %(message)s"
    )
    formatter = logging.Formatter(
        log_format,
        datefmt="%Y-%m-%d %H:%M:%S" # 时间戳格式
    )

    # --- 2. 获取根记录器 ---
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # 清除现有的处理器，避免重复日志
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # --- 3. 创建控制台处理器 ---
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)

    # --- 4. 创建文件处理器 ---
    # 创建 logs 目录（如果不存在）
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    # 使用当前日期命名日志文件，方便按天查找
    today = datetime.now().strftime("%Y%m%d")
    log_filename = os.path.join(log_dir, f"app_{today}.log")

    file_handler = logging.FileHandler(log_filename, mode='a', encoding='utf-8') # 'a' 表示追加模式
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)

    # --- 5. 将处理器添加到根记录器 ---
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # --- 6. (可选) 设置第三方库的日志级别 ---
    # 避免第三方库（如 requests, urllib3）的大量 DEBUG/INFO 日志干扰
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    # 如果你想减少 langgraph 自身的日志，可以设置
    # logging.getLogger("langgraph").setLevel(logging.WARNING)

    print(f"Logging configured. Logs will be written to '{log_filename}' and console.")
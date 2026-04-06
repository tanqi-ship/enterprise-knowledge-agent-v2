# ==============================
# 后端 Dockerfile（根目录）
# ==============================
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖（如果有 C 扩展库需要编译）
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 先复制依赖文件（利用 Docker 层缓存，依赖没变就不重新安装）
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# 复制全部项目文件
COPY . .

# 创建 logs 和 uploads 目录（容器内）
RUN mkdir -p /app/logs /app/uploads

# 暴露端口
EXPOSE 8000

# 启动命令（生产环境去掉 --reload）
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

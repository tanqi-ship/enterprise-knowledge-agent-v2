import os
from dotenv import load_dotenv
import psycopg2

# 1. 加载 .env 文件中的变量
load_dotenv()

# 2. 准备数据库配置
DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": os.getenv("POSTGRES_PORT", "5433"),  # 记得这里默认端口是 5433
    "dbname": os.getenv("POSTGRES_DB"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD")
}

print(f"正在尝试连接数据库: {DB_CONFIG['host']}:{DB_CONFIG['port']} ...")

try:
    # 3. 尝试连接
    conn = psycopg2.connect(**DB_CONFIG)

    # 4. 执行一个简单的查询
    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    db_version = cursor.fetchone()

    print("✅ 连接成功！")
    print(f"数据库版本: {db_version[0][:50]}...")

    cursor.close()
    conn.close()

except Exception as e:
    print("❌ 连接失败！")
    print(f"错误详情: {e}")
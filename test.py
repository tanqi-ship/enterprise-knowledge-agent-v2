
from backend.rag.store import _get_client
from backend.config import config

client = _get_client()
client.delete_collection(config.QDRANT_COLLECTION)
print("✅ 已清空，重新上传文件即可")
client.close()

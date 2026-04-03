import os
from fastapi import APIRouter, UploadFile, File, HTTPException
from backend.rag.ingest import ingest_file
from backend.rag.store import delete_by_source, list_sources

router = APIRouter(prefix="/documents", tags=["文档"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """上传文件并存入向量数据库"""
    allowed_ext = {".pdf", ".txt", ".docx", ".doc"}
    ext = os.path.splitext(file.filename)[1].lower()

    if ext not in allowed_ext:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式：{ext}，支持：{allowed_ext}"
        )

    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    return ingest_file(file_path)


@router.get("")
def list_documents():
    """列出已上传的文件（以 Qdrant 实际数据为准）"""
    sources = list_sources()  # ← 从 Qdrant 读，不从 uploads/ 读
    return {"documents": sources}


@router.delete("/{filename}")
def delete_document(filename: str):
    """删除文件及其向量数据"""

    # 1. 检查文件是否存在于 Qdrant
    sources = list_sources()
    if filename not in sources:
        raise HTTPException(status_code=404, detail=f"文件不存在：{filename}")

    # 2. 删除 Qdrant 里的向量数据
    delete_by_source(filename)

    # 3. 删除 uploads/ 里的原始文件
    file_path = os.path.join(UPLOAD_DIR, filename)
    if os.path.exists(file_path):
        os.remove(file_path)

    return {"status": "success", "message": f"{filename} 已删除"}

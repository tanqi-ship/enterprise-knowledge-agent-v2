# rag/loader.py
# 读取各种格式的文件，切割成小块

import os
from dataclasses import dataclass


@dataclass
class TextChunk:
    """一个文本块"""
    content: str        # 文本内容
    source: str         # 来源文件名
    chunk_index: int    # 第几块


def _split_text(text: str, source: str, chunk_size: int = 500, overlap: int = 50) -> list[TextChunk]:
    """
    把长文本切割成小块
    chunk_size: 每块最大字符数
    overlap:    相邻块之间重叠的字符数（避免关键信息被切断）
    """
    chunks = []
    start = 0
    index = 0

    while start < len(text):
        end = start + chunk_size
        chunk_text = text[start:end].strip()

        if chunk_text:
            chunks.append(TextChunk(
                content=chunk_text,
                source=source,
                chunk_index=index,
            ))
            index += 1

        # 下一块从 end - overlap 开始，保留重叠部分
        start = end - overlap

    return chunks


def load_txt(file_path: str) -> list[TextChunk]:
    """读取 TXT 文件"""
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()
    source = os.path.basename(file_path)
    return _split_text(text, source)


def load_pdf(file_path: str) -> list[TextChunk]:
    """读取 PDF 文件"""
    try:
        import pdfplumber
    except ImportError:
        raise ImportError("请先安装 pdfplumber: pip install pdfplumber")

    source = os.path.basename(file_path)
    text = ""

    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

    return _split_text(text, source)


def load_docx(file_path: str) -> list[TextChunk]:
    """读取 DOCX 文件"""
    try:
        from docx import Document
    except ImportError:
        raise ImportError("请先安装 python-docx: pip install python-docx")

    source = os.path.basename(file_path)
    doc = Document(file_path)
    text = "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
    return _split_text(text, source)


def load_doc(file_path: str) -> list[TextChunk]:
    """
    读取 DOC 文件（旧版 Word 格式）
    需要安装 antiword（Linux）或 依赖 Windows COM
    """
    try:
        import subprocess
        result = subprocess.run(
            ["antiword", file_path],
            capture_output=True, text=True
        )
        text = result.stdout
    except FileNotFoundError:
        raise RuntimeError(
            "读取 .doc 文件需要安装 antiword\n"
            "建议把 .doc 文件另存为 .docx 格式再上传"
        )

    source = os.path.basename(file_path)
    return _split_text(text, source)


# 根据文件扩展名自动选择读取方式
LOADERS = {
    ".txt": load_txt,
    ".pdf": load_pdf,
    ".docx": load_docx,
    ".doc": load_doc,
}


def load_file(file_path: str) -> list[TextChunk]:
    """
    自动识别文件格式并读取
    返回切割好的文本块列表
    """
    ext = os.path.splitext(file_path)[1].lower()
    loader = LOADERS.get(ext)

    if loader is None:
        raise ValueError(f"不支持的文件格式：{ext}，支持的格式：{list(LOADERS.keys())}")

    return loader(file_path)

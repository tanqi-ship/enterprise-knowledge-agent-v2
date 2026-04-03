import os
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from backend.agent import build_graph

router = APIRouter(prefix="/analyze", tags=["文档分析"])

# 复用已有的 agent
agent = build_graph()

# 单次分析不存文件，直接读内存
# 文档最大字符限制（约 2000 token）
MAX_CHARS = 6000


def extract_text(file: UploadFile) -> str:
    """从上传的文件中提取文本"""
    ext = os.path.splitext(file.filename)[1].lower()
    content = file.file.read()

    if ext == ".txt":
        return content.decode("utf-8", errors="ignore")

    elif ext in {".docx", ".doc"}:
        import docx
        from io import BytesIO
        doc = docx.Document(BytesIO(content))
        return "\n".join([para.text for para in doc.paragraphs if para.text.strip()])

    elif ext == ".pdf":
        import pdfplumber
        from io import BytesIO
        text = ""
        with pdfplumber.open(BytesIO(content)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text

    else:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式：{ext}，支持：txt / docx / pdf"
        )


@router.post("")
async def analyze_document(
    file: UploadFile = File(...),
    question: str = "请总结这篇文档的主要内容",
    thread_id: str = "analyze_temp",
):
    """
    上传文件 + 输入问题 → LLM 分析文档
    不存入知识库，仅用于即时分析
    """

    # 1. 提取文本
    text = extract_text(file)

    # 2. 检查长度，超出则截断
    truncated = False
    if len(text) > MAX_CHARS:
        text = text[:MAX_CHARS]
        truncated = True

    # 3. 拼接 prompt
    prompt = f"""以下是用户上传的文档内容：
------
{text}
------
请根据以上文档回答用户的问题：
{question}"""

    # 4. 发给 LLM
    config_dict = {"configurable": {"thread_id": thread_id}}
    input_state = {"messages": [HumanMessage(content=prompt)]}

    final_answer = ""
    for chunk, metadata in agent.stream(input_state, config_dict, stream_mode="messages"):
        if hasattr(chunk, "tool_calls") and not chunk.tool_calls and chunk.content:
            final_answer += chunk.content

    return {
        "answer": final_answer,
        "truncated": truncated,
        "char_count": len(text),
        "filename": file.filename,
    }

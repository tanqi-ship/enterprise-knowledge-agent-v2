# 企业知识代理系统
**登陆地址**：http://8.210.54.253/login

![项目演示1](https://github.com/user-attachments/assets/1bb79408-9b1f-40ba-9716-85c9151cb65f)


一个基于 AI 的企业知识管理与问答系统，采用 LangGraph 架构实现智能 Agent，支持多模态知识检索与交互。

## ✨ 功能特性

- 🧠 **智能 Agent**: 基于 LangGraph 的 ReAct 范式，可根据问题自动选择和调用不同工具
- 📚 **RAG 检索**: 支持上传文档至向量数据库，实现精准知识检索
- 🌐 **联网搜索**: 实时获取最新网络信息
- 🧠 **持久记忆**: 支持对话历史记录与上下文理解
- 🖥️  **日常问答**: 提供通用知识问答能力
- 🔐 **数据安全**: 保障企业数据安全

## 🛠️ 技术栈

### 后端
- **LangChain**: LLM 应用开发框架
- **LangGraph**: 图状智能 Agent 架构
- **FastAPI**: 高性能 Web 框架
- **ReAct 范式**: 推理与行动结合的 AI 范式

### 前端
- **Vue.js**: 渐进式 JavaScript 框架
- **Vite**: 下一代前端构建工具

### 数据存储
- **PostgreSQL**: 关系型数据库
- **Qdrant**: 向量数据库

### 部署
- **Docker**: 容器化部署
- **Docker Compose**: 多容器编排

## 🚀 快速开始

### 系统要求

- **云服务器**: 建议 2 核 4GB 内存及以上
- **Docker**: 版本 20.0+ 
- **Docker Compose**: 版本 2.0+

### 安装步骤

1. **克隆项目**
   ```bash
   git clone https://github.com/tanqi-ship/enterprise-knowledge-agent-v2.git
   cd enterprise-knowledge-agent-v2
   ```
2. **配置环境变量**
   ```bash
    cp example.env .env
   ```
编辑 .env 文件，填入必要的 API 密钥和配置：
需要在 .env 文件中配置以下内容（参考 example.env）：
- OPENAI_API_KEY: OpenAI API 密钥
- POSTGRES_DB: PostgreSQL 数据库名
- POSTGRES_USER: PostgreSQL 用户名
- POSTGRES_PASSWORD: PostgreSQL 密码
- QDRANT_URL: Qdrant 向量数据库地址
- 其他必要的 API 密钥和配置项
3. **构建项目**
    ```bash
    docker compose build
    docker compose up -d
    docker compose ps
    ```
   如果所有服务都正常运行，则表示安装成功,进入自己的公网ip访问
### 📋 使用指南
1. **日常问答**
- 直接输入问题即可获得 AI 回答
- 系统会利用预训练模型提供通用知识
2. **RAG 检索**
- 通过前端界面上传文档
- 文档将被索引到 Qdrant 向量数据库
- 提问时系统会检索相关文档内容
3. **联网搜索**
- 对于实时性要求高的问题
- 系统会自动调用联网搜索工具
4. **持久记忆**
- 系统会记住对话历史
- 支持上下文相关的连续对话
### 📊 架构设计
```
[用户请求] -> [FastAPI 网关] -> [LangGraph Agent] -> [工具调用]
                                ↓
                        [PostgreSQL + Qdrant]
                                ↓
                           [响应生成]
```

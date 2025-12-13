import json
import httpx
import sqlparse
from typing import List, Dict, Optional,Any   
from fastapi import HTTPException, status
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.log import log
from crud.crud_message import crud_message
from crud.crud_project import crud_project
from models.session import Session as SessionModel
from models.project import Project as ProjectModel
from schema.chat import ChatResponse, MessageType

# =========================================================
# 1. 模型配置注册表
# =========================================================
# 建议：长期来看，这些配置也可以移入数据库或 YAML，但目前作为常量定义在 Service 层是可以接受的
# 重点是 API Key 必须从 settings 读取

MODEL_REGISTRY = {
    "my-finetuned-sql": {
        "name": "My Fine-Tuned SQL Model",
        "api_url": "http://26.64.77.145:1234/v1/chat/completions", # 这里的IP如果是固定的可以留着，如果是变动的建议放config
        "model_id": "codellama/CodeLlama-13b-Instruct-hf",
        "api_key": "dummy-key", # 本地模型通常不需要 Key
        "type": "local_finetune"
    },
    "xiyan-sql": {
        "name": "XiYan-SQL (QwenCoder-32B)",
        "api_url": "https://api-inference.modelscope.cn/v1/chat/completions",
        "model_id": "XGenerationLab/XiYanSQL-QwenCoder-32B-2504",
        "api_key": settings.ai.modelscope_api_key, # <--- 修正：从配置读取
        "type": "general_llm"
    },
    "qwen-coder-32b": {
        "name": "Qwen2.5-Coder-32B",
        "api_url": "https://api-inference.modelscope.cn/v1/chat/completions",
        "model_id": "Qwen/Qwen2.5-Coder-32B-Instruct",
        "api_key": settings.ai.modelscope_api_key, # <--- 修正：从配置读取
        "type": "general_llm"
    },
    "deepseek-v3": {
        "name": "DeepSeek V3.1",
        "api_url": "https://api-inference.modelscope.cn/v1/chat/completions",
        "model_id": "deepseek-ai/DeepSeek-V3.1",
        "api_key": settings.ai.modelscope_api_key, # <--- 修正：从配置读取
        "type": "general_llm"
    }
}

DEFAULT_MODEL = "my-finetuned-sql"

# =========================================================
# 2. 辅助函数 (逻辑拆分)
# =========================================================

# src/backend/app/service/chat_service.py

def _format_schema_to_text(schema_data: Any) -> str:
    """
    将 Schema JSON 转换为模型易读的文本格式
    兼容 List 和 Dict 两种结构
    """
    if not schema_data:
        return ""
    try:
        # 1. 如果是字符串，先转成对象
        if isinstance(schema_data, str):
            schema_data = json.loads(schema_data)
        
        # 2. 【关键修复】如果是字典且包含 'tables' 键，提取出列表
        if isinstance(schema_data, dict) and "tables" in schema_data:
            schema_data = schema_data["tables"]

        # 3. 现在的 schema_data 应该是一个列表了，开始遍历
        lines = []
        if isinstance(schema_data, list):
            for table in schema_data:
                # 兼容 table 可能是 dict 或者 object 的情况
                if isinstance(table, dict):
                    t_name = table.get("table_name", "unknown")
                    cols = table.get("columns", [])
                else:
                    # 万一数据很怪，做一个容错
                    continue

                if isinstance(cols, str): 
                    cols = [cols]
                col_str = ", ".join(str(c) for c in cols)
                lines.append(f"Table: {t_name}, columns = [{col_str}]")
        else:
            # 如果结构实在太乱，直接转字符串兜底
            return str(schema_data)

        return "\n".join(lines)
    except Exception as e:
        log.error(f"Schema format error: {e}")
        # 出错了也不要崩，把原始数据给 AI，看它能不能看懂
        return str(schema_data)
    
def _build_ai_messages(model_config: Dict, schema_text: str, question: str) -> List[Dict]:
    """
    根据模型类型构建对应的 Prompt 策略
    解决“函数过长”问题，将 Prompt 逻辑抽离
    """
    if model_config["type"] == "local_finetune":
        # 策略 A: 微调模型 (严格格式)
        prompt_content = f"""I want you to act as a SQL terminal in front of an database.
Here is the schema:
{schema_text}

I want you to answer the following question.
### Question: {question}

### Response:
"""
        return [
            {"role": "system", "content": "You are a SQL expert."},
            {"role": "user", "content": prompt_content}
        ]
    else:
        # 策略 B: 通用大模型 (思维链与规则引导)
        system_prompt = f"""You are a generic SQL expert. 
Your task is to generate valid SQL queries based on the provided database schema and user question.

[Database Schema]
{schema_text}

[Important Rules]
1. The user asks in **Chinese**, but the table/column names are in **English**. You MUST map them semantically.
2. Respond **ONLY** with the SQL code. Do NOT wrap it in markdown code blocks.
3. Do NOT provide explanations.
4. If the logic involves 'JOIN', ensure column names are disambiguated.
5. Pay strict attention to column names in the schema. Do not hallucinate IDs.
"""
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question}
        ]

async def _verify_session_ownership(db: AsyncSession, session_id: int, user_id: int) -> int:
    """
    验证会话所有权，防止越权访问 (IDOR)
    返回: project_id
    """
    # 联表查询：Session -> Project，检查 Project.user_id 是否匹配
    stmt = (
        select(SessionModel)
        .options(selectinload(SessionModel.project)) # 预加载 Project 避免 N+1
        .where(SessionModel.session_id == session_id)
    )
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if not session.project:
        raise HTTPException(status_code=404, detail="Project not found for this session")

    # 【关键安全检查】
    if session.project.user_id != user_id:
        log.warning(f"Security Alert: User {user_id} tried to access session {session_id} belonging to user {session.project.user_id}")
        raise HTTPException(status_code=403, detail="Permission denied: You do not own this session")

    return session.project_id

# =========================================================
# 3. 核心业务逻辑
# =========================================================

async def call_ai_agent(schema_text: str, question: str, model_key: str = None) -> str:
    """
    调用 AI 接口生成 SQL
    """
    # 1. 确定配置
    if not model_key or model_key not in MODEL_REGISTRY:
        model_key = DEFAULT_MODEL
    
    config = MODEL_REGISTRY[model_key]
    log.info(f"Using AI Model: {config['name']} ({config['model_id']})")

    # 2. 构建 Prompt
    messages = _build_ai_messages(config, schema_text, question)

    # 3. 构建请求 Payload
    payload = {
        "model": config["model_id"],
        "messages": messages,
        "temperature": 0.1,
        "stream": False
    }
    
    if config["type"] == "general_llm":
        payload["max_tokens"] = 1024

    headers = {
        "Authorization": f"Bearer {config['api_key']}",
        "Content-Type": "application/json"
    }

    # 4. 执行网络请求
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(config["api_url"], json=payload, headers=headers)

        resp.raise_for_status()
        raw = resp.json()
        
        # 解析响应
        content = ""
        if "choices" in raw and len(raw["choices"]) > 0:
            content = raw["choices"][0]["message"]["content"]
        
        # 清理结果
        clean_sql = content.strip().replace("```sql", "").replace("```", "").strip()
        return clean_sql

    except Exception as e:
        log.error(f"AI Call Error ({model_key}): {e}")
        # 这里返回错误字符串是可以的，让用户知道 AI 挂了，而不是整个页面崩溃
        return f"-- AI Service Error: {str(e)}"


async def process_chat(
    db: AsyncSession, 
    session_id: int, 
    user_input: str, 
    user_id: int, 
    selected_model: str = None
) -> ChatResponse:
    """
    处理用户聊天请求的主流程
    """
    # 1. 安全检查：确认会话属于当前用户，并获取 project_id
    project_id = await _verify_session_ownership(db, session_id, user_id)

    # 2. 存用户消息 (先存库，保证有记录)
    await crud_message.create_message(db, session_id, user_input, role="user")

    # 3. 获取 Schema 上下文
    project = await crud_project.get(db, project_id)
    if not project or not project.schema_definition:
        schema_text = "No schema defined."
    else:
        schema_text = _format_schema_to_text(project.schema_definition)
    
    # 4. 调用 AI 生成 SQL
    sql_text = await call_ai_agent(schema_text, user_input, model_key=selected_model)

    # 5. 简单解析 SQL 类型
    sql_type = "UNKNOWN"
    try:
        if sql_text and not sql_text.startswith("--"):
            parsed = sqlparse.parse(sql_text)
            if parsed: 
                sql_type = parsed[0].get_type().upper()
    except Exception:
        pass

    # 6. 存 AI 回复消息
    reply_content = f"已生成查询语句：\n{sql_text}"
    ai_message = await crud_message.create_message(db, session_id, reply_content, role="assistant")

    # 7. 构造响应
    return ChatResponse(
        message_id=ai_message.message_id,
        content=reply_content, 
        message_type=MessageType.ASSISTANT,
        sql_text=sql_text,
        sql_type=sql_type,
        requires_confirmation=sql_type in ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER"],
        data=None
    )
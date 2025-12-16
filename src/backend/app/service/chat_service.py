"""
聊天服务。

处理与 AI 模型的聊天交互，负责 SQL 生成任务。
包含：
- 模型注册与配置管理
- 提示词工程 (Prompt Engineering)
- 会话所有权校验
- AI 响应的解析与格式化
- 会话模型记忆逻辑
"""

# backend/app/service/chat_service.py

import json
import httpx
import sqlparse
from typing import List, Dict, Any
from fastapi import HTTPException
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.log import log
from crud.crud_database_instance import crud_database_instance
from crud.crud_message import crud_message
from crud.crud_project import crud_project
from models.session import Session as SessionModel
from schema.chat import ChatResponse, MessageType
from service.mysql_service import execute_sql_with_user_check

# =========================================================
# 1. 模型配置注册表
# =========================================================

MODEL_REGISTRY = {
    "my-finetuned-sql": {
        "name": "My Fine-Tuned SQL Model",
        # 1. 填入云服务器地址 (保留 /v1/chat/completions)
        "api_url": "http://1.92.127.206:8080/v1/chat/completions", 
        "model_id": "codellama/CodeLlama-13b-Instruct-hf",
        # 2. 填入真实密钥
        "api_key": "sk-2025texttosql", 
        "type": "local_finetune"
    },

    "xiyan-sql": {
        "name": "XiYan-SQL (QwenCoder-32B)",
        "api_url": "https://api-inference.modelscope.cn/v1/chat/completions",
        "model_id": "XGenerationLab/XiYanSQL-QwenCoder-32B-2504",
        "api_key": settings.ai.modelscope_api_key, 
        "type": "general_llm"
    },
    "qwen-coder-32b": {
        "name": "Qwen2.5-Coder-32B",
        "api_url": "https://api-inference.modelscope.cn/v1/chat/completions",
        "model_id": "Qwen/Qwen2.5-Coder-32B-Instruct",
        "api_key": settings.ai.modelscope_api_key, 
        "type": "general_llm"
    },
    "deepseek-v3": {
        "name": "DeepSeek V3.1",
        "api_url": "https://api-inference.modelscope.cn/v1/chat/completions",
        "model_id": "deepseek-ai/DeepSeek-V3.1",
        "api_key": settings.ai.modelscope_api_key, 
        "type": "general_llm"
    }
}

DEFAULT_MODEL = "my-finetuned-sql"

# =========================================================
# 2. 辅助函数
# =========================================================

def _format_schema_to_text(schema_data: Any) -> str:
    """将 Schema JSON 转换为模型易读的文本格式 (兼容 List/Dict)"""
    if not schema_data:
        return ""
    try:
        if isinstance(schema_data, str):
            schema_data = json.loads(schema_data)
        
        if isinstance(schema_data, dict) and "tables" in schema_data:
            schema_data = schema_data["tables"]

        lines = []
        if isinstance(schema_data, list):
            for table in schema_data:
                if isinstance(table, dict):
                    t_name = table.get("table_name", "unknown")
                    cols = table.get("columns", [])
                else:
                    continue

                if isinstance(cols, str): 
                    cols = [cols]
                col_str = ", ".join(str(c) for c in cols)
                lines.append(f"Table: {t_name}, columns = [{col_str}]")
        else:
            return str(schema_data)

        return "\n".join(lines)
    except Exception as e:
        log.error(f"Schema format error: {e}")
        return str(schema_data)
    
def _build_ai_messages(model_config: Dict, schema_text: str, question: str) -> List[Dict]:
    """构建 Prompt 策略"""
    if model_config["type"] == "local_finetune":
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
    """验证会话所有权，防止越权"""
    stmt = (
        select(SessionModel)
        .options(selectinload(SessionModel.project))
        .where(SessionModel.session_id == session_id)
    )
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if not session.project:
        raise HTTPException(status_code=404, detail="Project not found for this session")

    if session.project.user_id != user_id:
        log.warning(f"Security Alert: User {user_id} tried to access session {session_id} belonging to user {session.project.user_id}")
        raise HTTPException(status_code=403, detail="Permission denied: You do not own this session")

    return session.project_id

async def call_ai_agent(schema_text: str, question: str, model_key: str = None) -> str:
    """调用 AI 接口生成 SQL"""
    
    # 1. 确定配置
    if not model_key or model_key not in MODEL_REGISTRY:
        model_key = DEFAULT_MODEL
    
    config = MODEL_REGISTRY[model_key]
    log.info(f"Using AI Model: {config['name']} ({config['model_id']})")

    messages = _build_ai_messages(config, schema_text, question)

    # 2. 构建 Payload
    payload = {
        "model": config["model_id"],
        "messages": messages,
        "temperature": 0.1,
        "stream": False,
        "max_tokens": 512,
        # 【新增】告诉模型看到这些符号就闭嘴
        "stop": ["<|im_end|>", "<|im_start|>", "User:", "Assistant:"]
    }

    headers = {
        "Authorization": f"Bearer {config['api_key']}",
        "Content-Type": "application/json"
    }

    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            resp = await client.post(config["api_url"], json=payload, headers=headers)

        resp.raise_for_status()
        raw = resp.json()
        
        content = ""
        if "choices" in raw and len(raw["choices"]) > 0:
            content = raw["choices"][0]["message"]["content"]
        
        # =====================================================
        # 【关键修复】清洗数据，截断废话
        # =====================================================
        # 1. 如果模型输出了停止符，只取前面的部分
        if "<|im_end|>" in content:
            content = content.split("<|im_end|>")[0]
        if "<|im_start|>" in content:
            content = content.split("<|im_start|>")[0]
            
        # 2. 有时候模型会把 SQL 写在 Markdown 块里，先去 Markdown
        clean_sql = content.strip().replace("```sql", "").replace("```", "").strip()
        
        # 3. 如果还是有多行，且第一行就是完整的 SQL (以分号结尾)，就只取第一行
        # 防止它在 SQL 后面通过换行继续自言自语
        if ";\n" in clean_sql:
             clean_sql = clean_sql.split(";\n")[0] + ";"
        elif clean_sql.count(";") > 1:
             # 如果有多条 SQL，只取第一条
             clean_sql = clean_sql.split(";")[0] + ";"
             
        return clean_sql

    except Exception as e:
        log.error(f"AI Call Error ({model_key}): {e}")
        return f"-- AI Service Error: {str(e)}"

# =========================================================
# 3. 核心业务逻辑 (含模型记忆)
# =========================================================

async def process_chat(
    db: AsyncSession, 
    session_id: int, 
    user_input: str, 
    user_id: int, 
    selected_model: str = None
) -> ChatResponse:
    """
    处理用户聊天请求的主流程。
    """
    # 1. 验证会话权限
    project_id = await _verify_session_ownership(db, session_id, user_id)

    # 2. 获取 Session 对象以处理模型记忆逻辑
    stmt = select(SessionModel).where(SessionModel.session_id == session_id)
    result = await db.execute(stmt)
    session_obj = result.scalar_one_or_none()
    
    if not session_obj:
         raise HTTPException(status_code=404, detail="Session lost")

    # =========================================================
    # 【核心逻辑优化】模型选择优先级策略
    # =========================================================
    final_model_key = DEFAULT_MODEL # 兜底

    if selected_model:
        # A. 如果用户本次明确指定了模型 -> 使用它，并更新到数据库（记忆）
        final_model_key = selected_model
        if session_obj.current_model != selected_model:
            session_obj.current_model = selected_model
            db.add(session_obj)
            await db.commit() # 保存记忆
            log.info(f"Session {session_id} model switched to: {selected_model}")

    elif session_obj.current_model:
        # B. 如果用户没指定，但数据库里有记忆 -> 使用记忆的模型
        final_model_key = session_obj.current_model
        log.info(f"Session {session_id} using stored model: {final_model_key}")
        
    else:
        # C. 既没指定也没记忆 -> 使用系统默认，并保存到数据库作为初始记忆
        final_model_key = DEFAULT_MODEL
        session_obj.current_model = DEFAULT_MODEL
        db.add(session_obj)
        await db.commit()
    # =========================================================

    # 3. 存用户消息
    await crud_message.create_message(db, session_id, user_input, role="user")

    # 4. 获取 Schema 上下文
    project = await crud_project.get(db, project_id)
    if not project or not project.schema_definition:
        schema_text = "No schema defined."
    else:
        schema_text = _format_schema_to_text(project.schema_definition)
    
    # 5. 调用 AI 生成 SQL (使用记忆或指定的模型)
    sql_text = await call_ai_agent(schema_text, user_input, model_key=final_model_key)

    # 6. 简单解析 SQL 类型
    sql_type = "UNKNOWN"
    try:
        if sql_text and not sql_text.startswith("--"):
            parsed = sqlparse.parse(sql_text)
            if parsed: 
                sql_type = parsed[0].get_type().upper()
    except Exception:
        pass

    # 7. 存 AI 回复消息
    reply_content = f"已生成查询语句：\n{sql_text}"
    ai_message = await crud_message.create_message(db, session_id, reply_content, role="assistant")

    # 8. 尝试执行 SQL
    data = []
    try:
        database_instance = await crud_database_instance.get(db, project.instance_id)
        # 注意：这里调用的是 execute_sql_with_user_check，它会检查 SQL 是否安全
        data = await execute_sql_with_user_check(sql_text, sql_type, database_instance)
    except Exception as e:
        log.info(f"SQL Execution Error (Safe to ignore if SQL is invalid): {str(e)}")

    # 9. 构造响应
    return ChatResponse(
        message_id=ai_message.message_id,
        content=reply_content, 
        message_type=MessageType.ASSISTANT,
        sql_text=sql_text,
        sql_type=sql_type,
        requires_confirmation=sql_type in ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER"],
        data=data
    )
"""
聊天服务。

处理与 AI 模型的聊天交互，负责 SQL 生成任务并持久化执行结果。
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
from datetime import date, datetime
from core.config import settings
from core.log import log
from crud.crud_database_instance import crud_database_instance
from crud.crud_message import crud_message
from crud.crud_project import crud_project
from models.session import Session as SessionModel
from schema.chat import ChatResponse, MessageType
from service.mysql_service import execute_sql_with_user_check

# 导入必要的模型类
from models.message import Message as MessageModel 
from models.project import Project as ProjectModel
from models.ai_generated_statement import AIGeneratedStatement 
from models.query_result import QueryResult

# =========================================================
# 1. 模型配置注册表
# =========================================================
MODEL_REGISTRY = {
    "my-finetuned-sql": {
        "name": "My Fine-Tuned SQL Model",
        "api_url": "http://1.92.127.206:8080/v1/chat/completions",
        "model_id": "codellama/CodeLlama-13b-Instruct-hf",
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

def _json_serializable(obj):
    """处理 JSON 序列化时的非标准对象"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

async def _save_query_execution_result(
    db: AsyncSession,
    message_id: int,
    sql_text: str,
    sql_type: str,
    data: List[Dict]
) -> None:
    """
    将 AI 生成的 SQL 和执行结果快照持久化到元数据库中。
    """
    try:
        # 1. 保存到 ai_generated_statement 表
        serializable_data = json.loads(
            json.dumps(data, default=_json_serializable)
        )

        statement = AIGeneratedStatement(
            message_id=message_id,
            statement_order=1,
            sql_text=sql_text,
            statement_type=sql_type,
            execution_status="success" if data else "failed",
            execution_result=serializable_data, # 使用处理后的数据
        )
        db.add(statement)
        await db.flush()

        if sql_type == "SELECT" and serializable_data:
            q_result = QueryResult(
                statement_id=statement.statement_id,
                result_data=serializable_data, # 使用处理后的数据
                data_summary=f"Snapshot for query: {sql_text[:50]}..."
            )
            db.add(q_result)
            
    except Exception as e:
        log.error(f"Failed to persist query result: {e}")
        # 确保发生错误时能够清理事务状态
        await db.rollback()
        raise e

def _build_ai_messages(model_config: Dict, schema_text: str, question: str) -> List[Dict]:
    """构建 Prompt 策略"""
    base_system_instruction = """You are a specialized SQL generation assistant.
Your ONLY task is to generate valid SQL queries based on the provided database schema and user question.
... (保持原有约束) ...
"""
    context_block = f"[Database DDL]\n{schema_text}"
    if model_config["type"] == "local_finetune":
        prompt_content = f"{base_system_instruction}\n{context_block}\n\n### User Question\n{question}\n\n### SQL Query\n"
        return [{"role": "system", "content": "You are a SQL expert."}, {"role": "user", "content": prompt_content}]
    else:
        full_system_prompt = f"{base_system_instruction}\n{context_block}"
        return [{"role": "system", "content": full_system_prompt}, {"role": "user", "content": question}]

async def _verify_session_ownership(db: AsyncSession, session_id: int, user_id: int) -> int:
    """权限校验"""
    stmt = select(SessionModel).options(selectinload(SessionModel.project)).where(SessionModel.session_id == session_id)
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()
    if not session or not session.project:
        raise HTTPException(status_code=404, detail="Session or Project not found")
    if session.project.user_id != user_id:
        raise HTTPException(status_code=403, detail="Permission denied")
    return session.project_id

async def call_ai_agent(ddl_text: str, question: str, model_key: str = None) -> str:
    """调用 AI 生成 SQL"""
    if not model_key or model_key not in MODEL_REGISTRY:
        model_key = DEFAULT_MODEL
    config = MODEL_REGISTRY[model_key]
    messages = _build_ai_messages(config, ddl_text, question)
    payload = {"model": config["model_id"], "messages": messages, "temperature": 0.1, "stream": False}
    headers = {"Authorization": f"Bearer {config['api_key']}", "Content-Type": "application/json"}
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            resp = await client.post(config["api_url"], content=json.dumps(payload, ensure_ascii=False).encode("utf-8"), headers=headers)
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        return content.strip().replace("```sql", "").replace("```", "").strip()
    except Exception as e:
        log.error(f"AI Call Error: {e}")
        return f"-- AI Service Error: {str(e)}"

# =========================================================
# 3. 核心业务逻辑
# =========================================================

async def process_chat(
    db: AsyncSession, 
    session_id: int, 
    user_input: str, 
    user_id: int, 
    selected_model: str = None
) -> ChatResponse:
    project_id = await _verify_session_ownership(db, session_id, user_id)
    stmt = select(SessionModel).where(SessionModel.session_id == session_id)
    result = await db.execute(stmt)
    session_obj = result.scalar_one_or_none()
    
    if selected_model:
        session_obj.current_model = selected_model
        db.add(session_obj)
        await db.commit()
    final_model_key = session_obj.current_model or DEFAULT_MODEL

    await crud_message.create_message(db, session_id, user_input, role="user")
    project = await crud_project.get(db, project_id)
    ddl_text = project.ddl_statement if project and project.ddl_statement else "-- Error: No DDL"
    
    sql_text = await call_ai_agent(ddl_text, user_input, model_key=final_model_key)
    
    sql_type = "UNKNOWN"
    try:
        parsed = sqlparse.parse(sql_text)
        if parsed: sql_type = parsed[0].get_type().upper()
    except: pass

    requires_confirm = sql_type in ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE"]
    reply_content = f"已生成查询语句：\n{sql_text}"
    ai_message = await crud_message.create_message(db, session_id, reply_content, role="assistant")

    if requires_confirm:
        ai_message.requires_confirmation = True
        db.add(ai_message)
        await db.commit()
    
    data = []
    if not requires_confirm:
        try:
            database_instance = await crud_database_instance.get(db, project.instance_id)
            raw_result = await execute_sql_with_user_check(sql_text, sql_type, database_instance)
            data = raw_result if isinstance(raw_result, list) else ([raw_result] if raw_result else [])
            
            # 【新增】非确认操作（如 SELECT），立即持久化结果快照
            if data:
                await _save_query_execution_result(db, ai_message.message_id, sql_text, sql_type, data)
                await db.commit() 
        except Exception as e:
            log.info(f"Execution Error: {str(e)}")

    return ChatResponse(
        message_id=ai_message.message_id, content=reply_content, 
        message_type=MessageType.ASSISTANT, sql_text=sql_text,
        sql_type=sql_type, requires_confirmation=requires_confirm, data=data
    )

async def confirm_and_execute_sql(
    db: AsyncSession,
    message_id: int,
    user_id: int
) -> ChatResponse:
    """用户确认执行某条消息中的 SQL"""
    # 1. 查找消息、会话及项目
    stmt = select(MessageModel).where(MessageModel.message_id == message_id)
    result = await db.execute(stmt)
    message = result.scalar_one_or_none()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    stmt_session = select(SessionModel).where(SessionModel.session_id == message.session_id)
    session_obj = (await db.execute(stmt_session)).scalar_one_or_none()
    project = await crud_project.get(db, session_obj.project_id)

    if project.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    if not message.requires_confirmation or message.user_confirmed:
        raise HTTPException(status_code=400, detail="Invalid confirmation request")

    # 2. 提取并清理 SQL
    sql_text = message.content.split("：\n")[-1].strip() if "：\n" in message.content else message.content.strip()
    sql_text = sql_text.replace("```sql", "").replace("```", "").strip()

    execute_res = []
    try:
        # 3. 执行 DML
        database_instance = await crud_database_instance.get(db, project.instance_id)
        raw_result = await execute_sql_with_user_check(sql_text, "DML", database_instance)
        execute_res = raw_result if isinstance(raw_result, list) else ([raw_result] if raw_result else [])
        
        # 【新增】确认执行后，将变更影响的快照持久化
        await _save_query_execution_result(db, message.message_id, sql_text, "DML_EXECUTED", execute_res)
        
        message.user_confirmed = True
        db.add(message)
        await db.commit()
    except Exception as e:
        log.error(f"Execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    return ChatResponse(
        message_id=message.message_id, content=message.content,
        message_type=MessageType.ASSISTANT, sql_text=sql_text,
        sql_type="DML_EXECUTED", requires_confirmation=False, data=execute_res
    )
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

# 【关键融合 1】必须导入这些模型类，否则确认接口无法运行
from models.message import Message as MessageModel 
from models.project import Project as ProjectModel

# =========================================================
# 1. 模型配置注册表 (保留同学的更新)
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
# 2. 辅助函数 (保留同学优化的 Prompt 策略)
# =========================================================

def _build_ai_messages(model_config: Dict, schema_text: str, question: str) -> List[Dict]:
    """构建高可读性、结构化的 Prompt 策略"""
    
    # 定义清晰的系统指令
    base_system_instruction = """You are a specialized SQL generation assistant.
Your ONLY task is to generate valid SQL queries based on the provided database schema and user question.

[Constraints]
1. Output **ONLY** the SQL code. No explanations, no markdown (```sql).
2. If the user asks in Chinese, map it semantically to the English schema.
3. Use the exact table and column names from the schema.
4. If the question cannot be answered with the schema, return SELECT 'ERROR: Cannot answer';
5. Always use single quotes ('value') for string literals. NEVER use double quotes ("value").

IMPORTANT: 
- For string literals, YOU MUST USE SINGLE QUOTES (').
- DO NOT use double quotes (") or quotes(`).

Examples:
Correct: SELECT * FROM users WHERE name = 'John';
Wrong:   SELECT * FROM users WHERE name = "John";
"""
    context_block = f"""[Database DDL]
{schema_text}"""

    if model_config["type"] == "local_finetune":
        # 微调模型通常对 User 消息中的上下文反应更好
        prompt_content = f"""{base_system_instruction}
{context_block}

### User Question
{question}

### SQL Query
"""
        return [
            {"role": "system", "content": "You are a SQL expert."},
            {"role": "user", "content": prompt_content}
        ]
    else:
        # 通用大模型
        full_system_prompt = f"{base_system_instruction}\n{context_block}"
        return [
            {"role": "system", "content": full_system_prompt},
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

async def call_ai_agent(ddl_text: str, question: str, model_key: str = None) -> str:
    """调用 AI 接口生成 SQL"""
    
    # 1. 确定配置
    if not model_key or model_key not in MODEL_REGISTRY:
        model_key = DEFAULT_MODEL
    
    config = MODEL_REGISTRY[model_key]
    log.info(f"Using AI Model: {config['name']} ({config['model_id']})")

    messages = _build_ai_messages(config, ddl_text, question)

    # 2. 构建 Payload
    payload = {
        "model": config["model_id"],
        "messages": messages,
        "temperature": 0.1,
        "stream": False,
        "max_tokens": 512,
        "stop": ["<|im_end|>", "<|im_start|>", "User:", "Assistant:"]
    }

    headers = {
        "Authorization": f"Bearer {config['api_key']}",
        "Content-Type": "application/json"
    }

    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            # 【保留同学的 UTF-8 修复】这很重要，防止中文乱码
            resp = await client.post(
                config["api_url"], 
                content=json.dumps(payload, ensure_ascii=False).encode("utf-8"), 
                headers=headers
            )

        resp.raise_for_status()
        raw = resp.json()
        
        content = ""
        if "choices" in raw and len(raw["choices"]) > 0:
            content = raw["choices"][0]["message"]["content"]
        
        # 清洗数据
        if "<|im_end|>" in content:
            content = content.split("<|im_end|>")[0]
        if "<|im_start|>" in content:
            content = content.split("<|im_start|>")[0]
            
        clean_sql = content.strip().replace("```sql", "").replace("```", "").strip()
        
        if ";\n" in clean_sql:
             clean_sql = clean_sql.split(";\n")[0] + ";"
        elif clean_sql.count(";") > 1:
             clean_sql = clean_sql.split(";")[0] + ";"
             
        return clean_sql

    except Exception as e:
        log.error(f"AI Call Error ({model_key}): {e}")
        return f"-- AI Service Error: {str(e)}"

# =========================================================
# 3. 核心业务逻辑 (融合版：含模型记忆 + 安全刹车)
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

    # 2. 获取 Session 对象
    stmt = select(SessionModel).where(SessionModel.session_id == session_id)
    result = await db.execute(stmt)
    session_obj = result.scalar_one_or_none()
    
    if not session_obj:
         raise HTTPException(status_code=404, detail="Session lost")

    # =========================================================
    # 模型选择优先级策略
    # =========================================================
    final_model_key = DEFAULT_MODEL
    if selected_model:
        final_model_key = selected_model
        if session_obj.current_model != selected_model:
            session_obj.current_model = selected_model
            db.add(session_obj)
            await db.commit()
            log.info(f"Session {session_id} model switched to: {selected_model}")
    elif session_obj.current_model:
        final_model_key = session_obj.current_model
        log.info(f"Session {session_id} using stored model: {final_model_key}")
    else:
        session_obj.current_model = DEFAULT_MODEL
        db.add(session_obj)
        await db.commit()

    # 3. 存用户消息
    await crud_message.create_message(db, session_id, user_input, role="user")

    # 4. 获取 DDL 上下文
    # 【符合需求】直接读取 project.ddl_statement，解决表名大小写敏感问题
    project = await crud_project.get(db, project_id)
    ddl_text = ""
    if project and project.ddl_statement:
        ddl_text = project.ddl_statement
        log.info(f"Using DDL for project {project_id} (Length: {len(ddl_text)})")
    else:
        log.warning(f"Project {project_id} has empty ddl_statement!")
        ddl_text = "-- Error: No DDL found for this project."

    # 5. 调用 AI 生成 SQL
    sql_text = await call_ai_agent(ddl_text, user_input, model_key=final_model_key)

    # 6. 解析 SQL 类型
    sql_type = "UNKNOWN"
    try:
        if sql_text and not sql_text.startswith("--"):
            parsed = sqlparse.parse(sql_text)
            if parsed: 
                sql_type = parsed[0].get_type().upper()
    except Exception:
        pass

    # 【关键融合 2】判断是否需要确认
    requires_confirm = sql_type in ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE"]

    # 7. 存 AI 回复消息
    reply_content = f"已生成查询语句：\n{sql_text}"
    ai_message = await crud_message.create_message(db, session_id, reply_content, role="assistant")

    # 【关键融合 3】如果需要确认，必须把状态写回数据库！
    # 同学的代码里漏了这一步，导致确认时会报 400
    if requires_confirm:
        ai_message.requires_confirmation = True
        db.add(ai_message)
        await db.commit()
        await db.refresh(ai_message)

    # 8. 尝试执行 SQL (带刹车)
    data = []
    
    # 【关键融合 4】只有不需要确认的操作，才立即执行
    # 同学的代码里直接执行了，这很危险
    if not requires_confirm:
        try:
            database_instance = await crud_database_instance.get(db, project.instance_id)
            # result 可能是一个列表(SELECT) 或 一个字典(INSERT/UPDATE)
            raw_result = await execute_sql_with_user_check(sql_text, sql_type, database_instance)
            
            # 【同学的优化】统一数据格式为 List[Dict]
            if isinstance(raw_result, dict):
                data = [raw_result]
            elif isinstance(raw_result, list):
                data = raw_result
            else:
                data = []
        except Exception as e:
            log.info(f"SQL Execution Error (Safe to ignore if SQL is invalid): {str(e)}")
    else:
        # 如果需要确认，跳过执行
        log.info(f"SQL requires confirmation ({sql_type}), skipping immediate execution.")

    # 9. 构造响应
    return ChatResponse(
        message_id=ai_message.message_id,
        content=reply_content, 
        message_type=MessageType.ASSISTANT,
        sql_text=sql_text,
        sql_type=sql_type,
        requires_confirmation=requires_confirm,
        data=data
    )

# =========================================================
# 4. 执行确认逻辑 (同学代码里缺失，这里必须补上)
# =========================================================

async def confirm_and_execute_sql(
    db: AsyncSession,
    message_id: int,
    user_id: int
) -> ChatResponse:
    """
    用户确认执行某条消息中的 SQL (通常是增删改操作)。
    【修复版】使用分步查询法，解决 AttributeError。
    """
    # 1. 第一步：查消息本身
    stmt = select(MessageModel).where(MessageModel.message_id == message_id)
    result = await db.execute(stmt)
    message = result.scalar_one_or_none()

    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    # 2. 第二步：查所属 Session
    stmt_session = select(SessionModel).where(SessionModel.session_id == message.session_id)
    result_session = await db.execute(stmt_session)
    session_obj = result_session.scalar_one_or_none()
    
    if not session_obj:
        raise HTTPException(status_code=404, detail="Session not found")

    # 3. 第三步：查所属 Project
    stmt_project = select(ProjectModel).where(ProjectModel.project_id == session_obj.project_id)
    result_project = await db.execute(stmt_project)
    project = result_project.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # --- 校验逻辑 ---
    if project.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    if not message.requires_confirmation:
        raise HTTPException(status_code=400, detail="This message does not require confirmation")

    if message.user_confirmed:
        raise HTTPException(status_code=400, detail="This operation has already been confirmed/executed")

    # 4. 提取 SQL 语句
    content = message.content
    sql_text = ""
    
    if "：\n" in content:
        sql_text = content.split("：\n")[-1].strip()
    else:
        sql_text = content.strip()

    sql_text = sql_text.replace("```sql", "").replace("```", "").strip()

    # 5. 执行 SQL (DML)
    execute_res = []
    try:
        database_instance = await crud_database_instance.get(db, project.instance_id)
        
        # 真正执行
        result = await execute_sql_with_user_check(sql_text, "UPDATE", database_instance)
        
        # 📦 统一包装成列表
        if isinstance(result, dict):
            execute_res = [result]
        elif isinstance(result, list):
            execute_res = result
        else:
            execute_res = []
        
        # 更新消息状态
        message.user_confirmed = True
        db.add(message)
        await db.commit()

        log.info(f"User {user_id} confirmed execution of message {message_id}")

    except Exception as e:
        log.error(f"Execution failed: {e}")
        raise HTTPException(status_code=500, detail=f"Execution failed: {str(e)}")

    # 6. 返回结果
    return ChatResponse(
        message_id=message.message_id,
        content=message.content,
        message_type=MessageType.ASSISTANT,
        sql_text=sql_text,
        sql_type="DML_EXECUTED",
        requires_confirmation=False,
        data=execute_res
    )
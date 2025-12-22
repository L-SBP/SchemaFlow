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
from fastapi.encoders import jsonable_encoder

from core.config import settings
from core.log import log
from crud.crud_database_instance import crud_database_instance
from crud.crud_message import crud_message
from crud.crud_project import crud_project
from models.session import Session as SessionModel
from schema.chat import ChatResponse, MessageType
from service.mysql_service import execute_mysql_sql_with_user_check
from models.ai_generated_statement import AIGeneratedStatement
from models.query_result import QueryResult

# 必须导入这些模型类，否则确认接口无法运行
from models.message import Message as MessageModel 
from models.project import Project as ProjectModel

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
            # 【保留 UTF-8 修复】这很重要，防止中文乱码
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
# 3. 核心业务逻辑 (融合版：含模型记忆 + 安全刹车)
# =========================================================

# backend/app/service/chat_service.py

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
    # 3. 模型选择优先级策略 (修复 'final_model_key' 未定义问题)
    # =========================================================
    final_model_key = DEFAULT_MODEL  # 默认兜底

    if selected_model:
        # A. 用户本次明确指定了模型
        final_model_key = selected_model
        if session_obj.current_model != selected_model:
            session_obj.current_model = selected_model
            db.add(session_obj)
            # 这里先不 commit，后面统一提交提高性能
    elif session_obj.current_model:
        # B. 使用数据库记忆的模型
        final_model_key = session_obj.current_model
    
    log.info(f"Session {session_id} using model: {final_model_key}")

    # 4. 存用户发送的原始消息 (SF6 上下文记忆的基础)
    await crud_message.create_message(db, session_id, user_input, role="user")

    # 5. 获取 DDL 上下文并调用 AI
    project = await crud_project.get(db, project_id)
    ddl_text = project.ddl_statement if project and project.ddl_statement else "-- No DDL found"
    if user_input.strip() in ["取消", "cancel", "Stop"]:
        return ChatResponse(
            message_id=0, # 指令消息不一定需要存入数据库
            content="好的，已为您取消当前操作。",
            message_type=MessageType.ASSISTANT,
            sql_text=None,
            sql_type="ACTION_CANCEL", # 自定义类型，前端据此显示不同 UI
            requires_confirmation=False,
            data=None
        )
    # 执行 Text-to-SQL
    sql_text = await call_ai_agent(ddl_text, user_input, model_key=final_model_key)
    is_meta_sql = any(kw in sql_text.upper() for kw in ["'CANCELED'", "'ERROR'"])
    
    if is_meta_sql:
        reply_content = "抱歉，我无法执行该操作或理解您的指令。请提供具体的业务需求（如：查询书籍）。"
        # 存一条不带 SQL 执行记录的消息
        ai_message = await crud_message.create_message(db, session_id, reply_content, role="assistant")
        await db.commit()
        return ChatResponse(
            message_id=ai_message.message_id,
            content=reply_content,
            message_type=MessageType.ASSISTANT,
            sql_text=None, # 不给 SQL，前端就不会出黑色代码框
            sql_type="ERROR_FEEDBACK",
            requires_confirmation=False,
            data=None # 不给数据，前端就不会画表格
        )
    # 6. 解析 SQL 类型与安全性校验 (SF3)
    sql_type = "UNKNOWN"
    try:
        if sql_text and not sql_text.startswith("--"):
            parsed = sqlparse.parse(sql_text)
            if parsed: 
                sql_type = parsed[0].get_type().upper()
                if sql_type == "UNKNOWN" and sql_text.strip().upper().startswith("SELECT"):
                    sql_type = "SELECT"
    except: pass

    requires_confirm = sql_type in ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE"]

    # 7. 【核心修复】：只创建一条 Assistant 消息，防止重复发消息
    reply_content = f"已生成sql语句：\n{sql_text}"
    ai_message = await crud_message.create_message(db, session_id, reply_content, role="assistant")

    # 8. 尝试执行 SQL (针对 DQL 查询)
    data = []
    execution_status = "pending"
    exec_type = "SELECT"
    
    if not requires_confirm:
        try:
            database_instance = await crud_database_instance.get(db, project.instance_id)
            exec_type = sql_type if sql_type != "UNKNOWN" else "SELECT"
            raw_result = await execute_mysql_sql_with_user_check(sql_text, exec_type, database_instance)
            
            # 统一数据格式为 List[Dict]
            if isinstance(raw_result, list): data = raw_result
            elif isinstance(raw_result, dict): data = [raw_result]
            
            execution_status = "success"
        except Exception as e:
            log.error(f"SQL Execution Error: {str(e)}")
            execution_status = "failed"
    else:
        # DML 操作，标记为需确认，前端会显示确认按钮
        log.info(f"SQL requires confirmation ({sql_type}), skipping immediate execution.")
        ai_message.requires_confirmation = True
        db.add(ai_message)
        execution_status = "pending"

    # 9. 【关键持久化】：使用 jsonable_encoder 处理日期并保存到子表 (SF9)
    safe_data = jsonable_encoder(data)
    new_statement = AIGeneratedStatement(
        message_id=ai_message.message_id,
        sql_text=sql_text,
        statement_type=sql_type,
        execution_status=execution_status,
        execution_result=safe_data, 
        statement_order=1
    )
    db.add(new_statement)

    # 9.1 先 flush 拿到 statement_id，再写 QueryResult（报表/历史查询的数据源）
    await db.flush()

    # 仅对“成功的查询类语句”落库 QueryResult，避免把 DML/失败结果作为报表数据源
    if execution_status == "success" and exec_type == "SELECT":
        query_result = QueryResult(
            statement_id=new_statement.statement_id,
            result_data=safe_data,
            data_summary=None,
            chart_type="table",
        )
        db.add(query_result)
    
    # 最后统一 commit 事务，保证数据一致性
    await db.commit() 

    return ChatResponse(
        message_id=ai_message.message_id,
        content=reply_content, 
        message_type=MessageType.ASSISTANT,
        sql_text=sql_text,
        sql_type=sql_type,
        requires_confirmation=ai_message.requires_confirmation,
        data=safe_data
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
        # 真正执行 DML
        result = await execute_mysql_sql_with_user_check(sql_text, "UPDATE", database_instance)
        execute_res = [result] if isinstance(result, dict) else result
        
        # 1. 更新消息确认状态
        message.user_confirmed = True
        db.add(message)

        # 2. 【关键：同步更新子表结果】
        # 找到该消息对应的 SQL 记录并把执行结果填进去
        stmt_query = select(AIGeneratedStatement).where(AIGeneratedStatement.message_id == message_id)
        stmt_res = await db.execute(stmt_query)
        db_stmt = stmt_res.scalar_one_or_none()
        
        if db_stmt:
            db_stmt.execution_result = execute_res
            db_stmt.execution_status = "success"
            db.add(db_stmt)

        await db.commit()
        log.info(f"User {user_id} executed DML and persisted results.")

    except Exception as e:
        log.error(f"Execution failed: {e}")
        
        # 1. 提取错误信息
        error_msg = str(e)
        if isinstance(e, HTTPException):
            error_msg = e.detail
            
        # 2. 构造错误提示内容
        content = f"❌ 执行失败：\n{error_msg}"
        
        # 3. 创建一条新的系统消息记录错误
        error_message = await crud_message.create_message(
            db=db, 
            session_id=message.session_id,
            content=content,
            role=MessageType.ASSISTANT
        )
        
        # 4. 返回这条错误消息，让前端显示
        return ChatResponse(
            message_id=error_message.message_id,
            content=error_message.content,
            message_type=MessageType.ASSISTANT,
            sql_text=None,
            sql_type="ERROR",
            requires_confirmation=False,
            data=None
        )

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
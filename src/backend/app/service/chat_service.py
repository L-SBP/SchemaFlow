"""
聊天服务。

处理与 AI 模型的聊天交互，负责 SQL 生成任务。
包含：
- 模型注册与配置管理
- 会话所有权校验
- AI 响应的解析与格式化
- 会话模型记忆逻辑

重构说明：
1. 将长 AI 调用移出数据库事务，确保连接池不会被耗尽
2. 拆分 process_chat 为多个小函数，每个函数控制在 50 行以内
3. Prompt 模板移至 core/prompts.py
"""

# backend/app/service/chat_service.py

import json
import httpx
import sqlparse
from typing import List, Dict, Any, Optional, Tuple
from fastapi import HTTPException
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.encoders import jsonable_encoder

from core.config import settings
from core.log import log
from core.prompts import build_ai_messages
from crud.crud_database_instance import crud_database_instance
from crud.crud_message import crud_message
from crud.crud_project import crud_project
from crud.crud_knowledge import crud_knowledge
from models.session import Session as SessionModel
from schema.chat import ChatResponse, MessageType
from service.mysql_service import execute_mysql_sql_with_user_check
from service.postgresql_service import execute_postgres_sql_with_user_check
from service.sqlite_service import execute_sqlite_sql_with_user_check as execute_sqlite
from models.ai_generated_statement import AIGeneratedStatement
from models.query_result import QueryResult
from models.message import Message as MessageModel 
from models.project import Project as ProjectModel
from models.domain_knowledge import DomainKnowledge


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
# 2. 会话与权限校验
# =========================================================

async def _verify_session_ownership(db: AsyncSession, session_id: int, user_id: int) -> int:
    """验证会话所有权，防止越权。返回 project_id。"""
    stmt = (
        select(SessionModel)
        .options(selectinload(SessionModel.project))
        .where(SessionModel.session_id == session_id)
    )
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="会话未找到")
    
    if not session.project:
        raise HTTPException(status_code=404, detail="此会话的项目未找到")

    if session.project.user_id != user_id:
        log.warning(f"Security Alert: User {user_id} tried to access session {session_id}")
        raise HTTPException(status_code=403, detail="权限拒绝")

    return session.project_id


async def _get_session_obj(db: AsyncSession, session_id: int) -> SessionModel:
    """获取会话对象。"""
    stmt = select(SessionModel).where(SessionModel.session_id == session_id)
    result = await db.execute(stmt)
    session_obj = result.scalar_one_or_none()
    if not session_obj:
        raise HTTPException(status_code=404, detail="会话已丢失")
    return session_obj


# =========================================================
# 3. 模型选择策略
# =========================================================

def _resolve_model_key(
    selected_model: Optional[str],
    session_current_model: Optional[str]
) -> str:
    """
    解析最终使用的模型 key。
    优先级：用户本次指定 > 会话记忆 > 默认模型
    """
    if selected_model and selected_model in MODEL_REGISTRY:
        return selected_model
    if session_current_model and session_current_model in MODEL_REGISTRY:
        return session_current_model
    return DEFAULT_MODEL


async def _update_session_model(
    db: AsyncSession,
    session_obj: SessionModel,
    new_model: str
) -> None:
    """更新会话的当前模型（如果有变化）。"""
    if session_obj.current_model != new_model:
        session_obj.current_model = new_model
        db.add(session_obj)


# =========================================================
# 4. AI 调用（事务外执行）
# =========================================================

# TODO: [Celery] AI 调用任务化（可选）
# 当前实现：同步等待 AI 响应（最长 300s）
# 后续优化场景：
#   1. 对于复杂查询，可迁移到 Celery 异步执行
#   2. 前端显示 "生成中..." 加载状态，通过 WebSocket 推送结果
#   3. 支持用户取消正在进行的 AI 调用
#   4. 记录 AI 调用耗时，用于性能监控
# 注意：大多数场景可保持同步，用户体验更好

def _clean_ai_response(content: str) -> str:
    """清洗 AI 返回的 SQL 内容。"""
    # 移除停止符
    for stop_token in ["<|im_end|>", "<|im_start|>"]:
        if stop_token in content:
            content = content.split(stop_token)[0]
    
    # 去除 Markdown 标记
    clean_sql = content.strip().replace("```sql", "").replace("```", "").strip()
    
    # 只取第一条 SQL
    if ";\n" in clean_sql:
        clean_sql = clean_sql.split(";\n")[0] + ";"
    elif clean_sql.count(";") > 1:
        clean_sql = clean_sql.split(";")[0] + ";"
    
    return clean_sql


async def call_ai_agent(
    ddl_text: str,
    question: str,
    history: List[MessageModel] = None,
    knowledge: List[DomainKnowledge] = None,
    model_key: str = None
) -> str:
    """
    调用 AI 接口生成 SQL。
    
    【重要】此函数不应在数据库事务内调用，因为 AI 调用可能耗时很长（最长 300s）。
    """
    history = history or []
    knowledge = knowledge or []
    
    if not model_key or model_key not in MODEL_REGISTRY:
        model_key = DEFAULT_MODEL
    
    config = MODEL_REGISTRY[model_key]
    log.info(f"Using AI Model: {config['name']} ({config['model_id']})")

    messages = build_ai_messages(
        model_type=config["type"],
        schema_text=ddl_text,
        question=question,
        history=history,
        knowledge=knowledge
    )

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
        
        return _clean_ai_response(content)

    except Exception as e:
        log.error(f"AI Call Error ({model_key}): {e}")
        return f"-- AI Service Error: {str(e)}"


# =========================================================
# 5. SQL 解析与执行
# =========================================================

def _parse_sql_type(sql_text: str) -> str:
    """解析 SQL 语句类型。"""
    sql_type = "UNKNOWN"
    try:
        if sql_text and not sql_text.startswith("--"):
            parsed = sqlparse.parse(sql_text)
            if parsed:
                sql_type = parsed[0].get_type().upper()
                if sql_type == "UNKNOWN" and sql_text.strip().upper().startswith("SELECT"):
                    sql_type = "SELECT"
    except Exception:
        pass
    return sql_type


def _is_meta_sql(sql_text: str) -> bool:
    """判断是否为元数据/错误 SQL。"""
    return any(kw in sql_text.upper() for kw in ["'CANCELED'", "'ERROR'"])


def _requires_confirmation(sql_type: str) -> bool:
    """判断 SQL 类型是否需要用户确认。"""
    return sql_type in ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE"]


async def _execute_sql_by_type(sql: str, sql_type: str, instance: Any, user_id: int):
    """根据数据库类型分发执行逻辑。"""
    if instance.db_type == 'mysql':
        return await execute_mysql_sql_with_user_check(sql, sql_type, instance)
    elif instance.db_type == 'postgresql':
        return await execute_postgres_sql_with_user_check(sql, sql_type, instance)
    elif instance.db_type == 'sqlite':
        return await execute_sqlite(sql, sql_type, instance, user_id)
    else:
        raise HTTPException(status_code=400, detail=f"不支持的数据库类型: {instance.db_type}")


# =========================================================
# 6. 消息持久化（独立事务）
# =========================================================

async def _save_user_message(
    db: AsyncSession,
    session_id: int,
    content: str
) -> MessageModel:
    """保存用户消息（独立事务）。"""
    return await crud_message.create_message(db, session_id, content, role="user")


async def _save_ai_response(
    db: AsyncSession,
    session_id: int,
    sql_text: str,
    sql_type: str,
    requires_confirm: bool,
    execution_status: str,
    data: List[Dict]
) -> Tuple[MessageModel, AIGeneratedStatement]:
    """
    保存 AI 响应和执行结果（独立事务）。
    """
    reply_content = f"已生成sql语句：\n{sql_text}"
    ai_message = await crud_message.create_message(db, session_id, reply_content, role="assistant")
    
    if requires_confirm:
        ai_message.requires_confirmation = True
        db.add(ai_message)

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
    await db.flush()

    # 仅对成功的查询落库 QueryResult
    if execution_status == "success" and sql_type == "SELECT":
        query_result = QueryResult(
            statement_id=new_statement.statement_id,
            result_data=safe_data,
            data_summary=None,
            chart_type="table",
        )
        db.add(query_result)
    
    await db.commit()
    return ai_message, new_statement


# =========================================================
# 7. 核心业务逻辑（重构后）
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
    
    【原子性修复】将流程拆分为三个阶段：
    1. 事务1：保存用户消息，获取上下文
    2. 事务外：调用 AI（长连接，最长 300s）
    3. 事务2：保存 AI 响应和执行结果
    """
    # === 阶段1：验证权限并获取上下文 ===
    project_id = await _verify_session_ownership(db, session_id, user_id)
    session_obj = await _get_session_obj(db, session_id)
    
    # 解析模型
    final_model_key = _resolve_model_key(selected_model, session_obj.current_model)
    await _update_session_model(db, session_obj, final_model_key)
    log.info(f"Session {session_id} using model: {final_model_key}")
    
    # 获取历史和领域知识
    # TODO: [RAG] 历史对话检索优化
    # 当前实现：简单获取最近 20 条消息
    # 后续优化：
    #   1. 将历史消息向量化存储（Embedding）
    #   2. 根据当前 user_input 进行语义相似度检索
    #   3. 只召回与当前问题相关的历史对话（Top-K）
    #   4. 考虑时间衰减因子，近期对话权重更高
    # TODO: [Celery] 向量索引后台更新
    #   1. 消息保存后，异步触发 Embedding 生成任务
    #   2. 使用 Celery 任务将向量写入向量数据库（Milvus/Qdrant）
    #   3. 支持批量向量化，减少 API 调用次数
    history_context = await crud_message.get_recent_messages(db, session_id, limit=20)
    
    # TODO: [RAG] 领域知识检索优化
    # 当前实现：全量获取项目下所有领域知识
    # 后续优化：
    #   1. 将领域知识（term + definition）向量化存储
    #   2. 根据 user_input 语义检索相关术语（Top-K）
    #   3. 避免 Context 溢出，只注入相关知识
    #   4. 支持知识库的增量更新和索引重建
    # TODO: [Celery] 知识库向量化后台任务
    #   1. 知识条目创建/更新时，异步触发 Embedding 生成
    #   2. 支持批量导入知识时的后台向量化
    #   3. 知识库索引重建任务（切换 Embedding 模型时）
    knowledge_context = await crud_knowledge.get_all_by_project(db, project_id)
    
    # 保存用户消息
    await _save_user_message(db, session_id, user_input)
    
    # 获取 DDL
    # TODO: [RAG] Schema/DDL 检索优化（针对大型数据库）
    # 当前实现：全量注入完整 DDL
    # 后续优化（当表数量 > 阈值时启用）：
    #   1. 将每张表的 DDL 片段单独向量化
    #   2. 根据 user_input 检索相关表（Top-K）
    #   3. 只注入相关表的 DDL，减少 Token 消耗
    #   4. 保留表间外键关系的完整性
    # TODO: [Celery] DDL 向量化后台任务
    #   1. 项目部署成功后，异步触发 DDL 分片 + 向量化
    #   2. DDL 变更时自动更新向量索引
    #   3. 支持增量更新，避免全量重建
    project = await crud_project.get(db, project_id)
    ddl_text = project.ddl_statement if project and project.ddl_statement else "-- No DDL found"
    instance_id = project.instance_id
    
    # 提交事务1，释放数据库连接
    await db.commit()
    
    # 检查取消指令
    if user_input.strip() in ["取消", "cancel", "Stop"]:
        return _build_cancel_response()
    
    # === 阶段2：调用 AI（事务外，长连接） ===
    sql_text = await call_ai_agent(
        ddl_text,
        user_input,
        history=history_context,
        knowledge=knowledge_context,
        model_key=final_model_key
    )
    
    # 检查元数据 SQL
    if _is_meta_sql(sql_text):
        return await _handle_meta_sql_response(db, session_id)
    
    # === 阶段3：解析、执行、持久化 ===
    sql_type = _parse_sql_type(sql_text)
    requires_confirm = _requires_confirmation(sql_type)
    
    data = []
    execution_status = "pending"
    
    if not requires_confirm:
        data, execution_status = await _try_execute_sql(
            db, sql_text, sql_type, instance_id, user_id
        )
    
    ai_message, _ = await _save_ai_response(
        db, session_id, sql_text, sql_type, requires_confirm, execution_status, data
    )
    
    return ChatResponse(
        message_id=ai_message.message_id,
        content=f"已生成sql语句：\n{sql_text}",
        message_type=MessageType.ASSISTANT,
        sql_text=sql_text,
        sql_type=sql_type,
        requires_confirmation=requires_confirm,
        data=jsonable_encoder(data)
    )


def _build_cancel_response() -> ChatResponse:
    """构建取消操作的响应。"""
    return ChatResponse(
        message_id=0,
        content="好的，已为您取消当前操作。",
        message_type=MessageType.ASSISTANT,
        sql_text=None,
        sql_type="ACTION_CANCEL",
        requires_confirmation=False,
        data=None
    )


async def _handle_meta_sql_response(db: AsyncSession, session_id: int) -> ChatResponse:
    """处理元数据/错误 SQL 的响应。"""
    reply_content = "抱歉，我无法执行该操作或理解您的指令。请提供具体的业务需求（如：查询书籍）。"
    ai_message = await crud_message.create_message(db, session_id, reply_content, role="assistant")
    await db.commit()
    
    return ChatResponse(
        message_id=ai_message.message_id,
        content=reply_content,
        message_type=MessageType.ASSISTANT,
        sql_text=None,
        sql_type="ERROR_FEEDBACK",
        requires_confirmation=False,
        data=None
    )


async def _try_execute_sql(
    db: AsyncSession,
    sql_text: str,
    sql_type: str,
    instance_id: int,
    user_id: int
) -> Tuple[List[Dict], str]:
    """尝试执行 SQL 并返回结果和状态。"""
    try:
        database_instance = await crud_database_instance.get(db, instance_id)
        exec_type = sql_type if sql_type != "UNKNOWN" else "SELECT"
        raw_result = await _execute_sql_by_type(sql_text, exec_type, database_instance, user_id)
        
        if isinstance(raw_result, list):
            data = raw_result
        elif isinstance(raw_result, dict):
            data = [raw_result]
        else:
            data = []
        
        return data, "success"
    except Exception as e:
        log.error(f"SQL Execution Error: {str(e)}")
        return [], "failed"


# =========================================================
# 8. 确认执行逻辑
# =========================================================

async def _get_message_context(
    db: AsyncSession,
    message_id: int
) -> Tuple[MessageModel, SessionModel, ProjectModel]:
    """获取消息相关的上下文对象。"""
    stmt = select(MessageModel).where(MessageModel.message_id == message_id)
    result = await db.execute(stmt)
    message = result.scalar_one_or_none()
    if not message:
        raise HTTPException(status_code=404, detail="消息未找到")

    stmt_session = select(SessionModel).where(SessionModel.session_id == message.session_id)
    result_session = await db.execute(stmt_session)
    session_obj = result_session.scalar_one_or_none()
    if not session_obj:
        raise HTTPException(status_code=404, detail="Session not found")

    stmt_project = select(ProjectModel).where(ProjectModel.project_id == session_obj.project_id)
    result_project = await db.execute(stmt_project)
    project = result_project.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="项目未找到")

    return message, session_obj, project


def _validate_confirmation(message: MessageModel, project: ProjectModel, user_id: int) -> None:
    """验证确认操作的合法性。"""
    if project.user_id != user_id:
        raise HTTPException(status_code=403, detail="访问拒绝")
    if not message.requires_confirmation:
        raise HTTPException(status_code=400, detail="此消息不需要确认")
    if message.user_confirmed:
        raise HTTPException(status_code=400, detail="已确认/执行")


def _extract_sql_from_content(content: str) -> str:
    """从消息内容中提取 SQL。"""
    sql_text = ""
    if "：\n" in content:
        sql_text = content.split("：\n")[-1].strip()
    else:
        sql_text = content.strip()
    return sql_text.replace("```sql", "").replace("```", "").strip()


async def _update_statement_result(
    db: AsyncSession,
    message_id: int,
    execute_res: List[Dict]
) -> None:
    """更新 SQL 语句的执行结果。"""
    stmt_query = select(AIGeneratedStatement).where(AIGeneratedStatement.message_id == message_id)
    stmt_res = await db.execute(stmt_query)
    db_stmt = stmt_res.scalar_one_or_none()
    
    if db_stmt:
        db_stmt.execution_result = execute_res
        db_stmt.execution_status = "success"
        db.add(db_stmt)


async def _handle_execution_error(
    db: AsyncSession,
    session_id: int,
    error: Exception
) -> ChatResponse:
    """处理执行错误并返回错误响应。"""
    error_msg = str(error)
    if isinstance(error, HTTPException):
        error_msg = error.detail
    
    content = f"❌ 执行失败：\n{error_msg}"
    error_message = await crud_message.create_message(
        db=db,
        session_id=session_id,
        content=content,
        role=MessageType.ASSISTANT
    )
    
    return ChatResponse(
        message_id=error_message.message_id,
        content=error_message.content,
        message_type=MessageType.ASSISTANT,
        sql_text=None,
        sql_type="ERROR",
        requires_confirmation=False,
        data=None
    )


async def confirm_and_execute_sql(
    db: AsyncSession,
    message_id: int,
    user_id: int
) -> ChatResponse:
    """
    用户确认执行某条消息中的 SQL (通常是增删改操作)。
    """
    # 获取上下文
    message, session_obj, project = await _get_message_context(db, message_id)
    
    # 验证
    _validate_confirmation(message, project, user_id)
    
    # 提取 SQL
    sql_text = _extract_sql_from_content(message.content)
    
    # 执行
    try:
        database_instance = await crud_database_instance.get(db, project.instance_id)
        result = await _execute_sql_by_type(sql_text, "UPDATE", database_instance, user_id)
        execute_res = [result] if isinstance(result, dict) else result
        
        message.user_confirmed = True
        db.add(message)
        
        await _update_statement_result(db, message_id, execute_res)
        await db.commit()
        
        log.info(f"User {user_id} executed DML and persisted results.")
        
    except Exception as e:
        log.error(f"Execution failed: {e}")
        return await _handle_execution_error(db, message.session_id, e)

    return ChatResponse(
        message_id=message.message_id,
        content=message.content,
        message_type=MessageType.ASSISTANT,
        sql_text=sql_text,
        sql_type="DML_EXECUTED",
        requires_confirmation=False,
        data=execute_res
    )

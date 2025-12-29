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
4. 模型配置支持从数据库动态读取，硬编码配置作为后备
"""

# backend/app/service/chat_service.py

import json
import httpx
import sqlparse
from typing import List, Dict, Any, Optional, Tuple
from fastapi import HTTPException
from sqlalchemy.future import select
from sqlalchemy import update
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.encoders import jsonable_encoder
from core.exceptions import ForbiddenException, ItemNotFoundException, InvalidOperationException, BusinessException, AppException

from core.config import settings
from core.log import log
from core.prompts import build_ai_messages
from crud.crud_database_instance import crud_database_instance
from crud.crud_message import crud_message
from crud.crud_project import crud_project
from crud.crud_knowledge import crud_knowledge
from crud.crud_ai_model_config import crud_ai_model_config
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

# RAG 服务导入
from service.rag_service import rag_service, retrieve_chat_context, index_new_message


# =========================================================
# 1. 模型配置注册表（后备配置，当数据库无配置时使用）
# =========================================================

FALLBACK_MODEL_REGISTRY = {
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

# 保留旧变量名以兼容可能的外部引用
MODEL_REGISTRY = FALLBACK_MODEL_REGISTRY

DEFAULT_MODEL = "my-finetuned-sql"


# =========================================================
# 1.1 动态模型配置获取
# =========================================================

async def get_model_registry(db: AsyncSession) -> Dict[str, Dict[str, Any]]:
    """
    获取模型配置注册表。

    优先从数据库读取，如果数据库无配置则使用后备配置。

    Args:
        db (AsyncSession): 数据库会话。

    Returns:
        Dict[str, Dict[str, Any]]: 模型配置字典。
    """
    try:
        db_registry = await crud_ai_model_config.get_model_registry(db)
        if db_registry:
            return db_registry
    except Exception as e:
        log.warning(f"Failed to load model config from database: {e}, using fallback")

    return FALLBACK_MODEL_REGISTRY


async def get_default_model_key(db: AsyncSession) -> str:
    """
    获取默认模型名称。

    由于移除了 is_default 字段，这里返回第一个配置的模型名称。
    如果数据库无配置则使用后备默认值。

    Args:
        db (AsyncSession): 数据库会话。

    Returns:
        str: 默认模型名称。
    """
    try:
        configs = await crud_ai_model_config.get_all(db, limit=1)
        if configs:
            return configs[0].model_name
    except Exception as e:
        log.warning(f"Failed to load default model from database: {e}, using fallback")

    return DEFAULT_MODEL


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
        raise ItemNotFoundException(message="会话未找到")
    
    if not session.project:
        raise ItemNotFoundException(message="此会话的项目未找到")

    if session.project.user_id != user_id:
        log.warning("Security Alert: User {} tried to access session {}", user_id, session_id)
        raise ForbiddenException(message="权限拒绝")

    return session.project_id


async def _get_session_obj(db: AsyncSession, session_id: int) -> SessionModel:
    """获取会话对象。"""
    stmt = select(SessionModel).where(SessionModel.session_id == session_id)
    result = await db.execute(stmt)
    session_obj = result.scalar_one_or_none()
    if not session_obj:
        raise ItemNotFoundException(message="会话已丢失")
    return session_obj


# =========================================================
# 3. 模型选择策略
# =========================================================

async def _resolve_model_key(
    db: AsyncSession,
    selected_model: Optional[str],
    session_current_model: Optional[str]
) -> Tuple[str, Dict[str, Dict[str, Any]]]:
    """
    解析最终使用的模型 key。
    优先级：用户本次指定 > 会话记忆 > 默认模型

    同时返回模型注册表，避免重复查询数据库。

    Returns:
        Tuple[str, Dict]: (模型 key, 模型配置注册表)
    """
    # 获取模型注册表
    registry = await get_model_registry(db)
    default_key = await get_default_model_key(db)

    if selected_model and selected_model in registry:
        return selected_model, registry
    if session_current_model and session_current_model in registry:
        return session_current_model, registry

    return default_key, registry


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
# 3.1 RAG 结果转换辅助函数
# =========================================================

async def _convert_rag_history_to_messages(
    db: AsyncSession,
    rag_results: List[Dict[str, Any]]
) -> List[MessageModel]:
    """
    将 RAG 检索的历史结果转换为 MessageModel 兼容格式。
    
    Args:
        db: 数据库会话
        rag_results: RAG 检索结果列表
        
    Returns:
        List[MessageModel]: 消息列表
    """
    if not rag_results:
        return []
    
    # 从 RAG 结果中提取 message_id
    message_ids = []
    for result in rag_results:
        metadata = result.get("metadata", {})
        msg_id = metadata.get("message_id")
        if msg_id:
            message_ids.append(msg_id)
    
    if not message_ids:
        return []
    
    # 从数据库获取完整的消息对象
    from sqlalchemy import select
    stmt = select(MessageModel).where(MessageModel.message_id.in_(message_ids))
    result = await db.execute(stmt)
    messages = result.scalars().all()
    
    # 按 RAG 相关性顺序排序（保持检索顺序）
    message_map = {msg.message_id: msg for msg in messages}
    ordered_messages = []
    for result in rag_results:
        msg_id = result.get("metadata", {}).get("message_id")
        if msg_id and msg_id in message_map:
            ordered_messages.append(message_map[msg_id])
    
    return ordered_messages


async def _convert_rag_knowledge_to_domain(
    db: AsyncSession,
    rag_results: List[Dict[str, Any]]
) -> List[DomainKnowledge]:
    """
    将 RAG 检索的知识结果转换为 DomainKnowledge 兼容格式。
    
    Args:
        db: 数据库会话
        rag_results: RAG 检索结果列表
        
    Returns:
        List[DomainKnowledge]: 领域知识列表
    """
    if not rag_results:
        return []
    
    # 从 RAG 结果中提取 knowledge_id
    knowledge_ids = []
    for result in rag_results:
        metadata = result.get("metadata", {})
        k_id = metadata.get("knowledge_id")
        if k_id:
            knowledge_ids.append(k_id)
    
    if not knowledge_ids:
        return []
    
    # 从数据库获取完整的知识对象
    from sqlalchemy import select
    stmt = select(DomainKnowledge).where(DomainKnowledge.knowledge_id.in_(knowledge_ids))
    result = await db.execute(stmt)
    knowledge_items = result.scalars().all()
    
    # 按 RAG 相关性顺序排序
    knowledge_map = {k.knowledge_id: k for k in knowledge_items}
    ordered_knowledge = []
    for result in rag_results:
        k_id = result.get("metadata", {}).get("knowledge_id")
        if k_id and k_id in knowledge_map:
            ordered_knowledge.append(knowledge_map[k_id])
    
    return ordered_knowledge


# =========================================================
# 4. AI 调用（事务外执行）
# =========================================================


# 注意：大多数场景可保持同步，用户体验更好

def _clean_ai_response(content: str) -> str:
    """清洗 AI 返回的 SQL 内容。"""
    # 移除所有可能的停止符（INST 格式 + ChatML 格式兜底）
    stop_tokens = [
        "[/INST]", "[INST]", "<<SYS>>", "<</SYS>>",
        "<|im_end|>", "<|im_start|>",  # ChatML 格式兜底清理
        "<|endoftext|>", "<|end|>", "</s>", "<s>"
    ]
    for stop_token in stop_tokens:
        if stop_token in content:
            content = content.split(stop_token)[0]
    
    # 去除 Markdown 标记
    clean_sql = content.strip().replace("```sql", "").replace("```", "").strip()
    
    # 移除可能的前缀文本（如"已生成sql语句："等）
    prefixes_to_remove = [
        "已生成sql语句：",
        "已生成SQL语句：", 
        "生成的SQL语句：",
        "SQL语句：",
        "查询语句："
    ]
    
    for prefix in prefixes_to_remove:
        if clean_sql.startswith(prefix):
            clean_sql = clean_sql[len(prefix):].strip()
    
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
    model_key: str = None,
    model_registry: Dict[str, Dict[str, Any]] = None,
    db_type: str = None
) -> str:
    """
    调用 AI 接口生成 SQL。
    
    【重要】此函数不应在数据库事务内调用，因为 AI 调用可能耗时很长（最长 300s）。

    Args:
        ddl_text: 数据库 DDL 语句
        question: 用户问题
        history: 历史消息列表
        knowledge: 领域知识列表
        model_key: 模型标识符
        model_registry: 模型配置注册表（从数据库或后备配置获取）
        db_type: 数据库类型（mysql/postgresql/sqlite）
    """
    history = history or []
    knowledge = knowledge or []
    
    # 使用传入的注册表或后备配置
    registry = model_registry or FALLBACK_MODEL_REGISTRY
    
    if not model_key or model_key not in registry:
        model_key = DEFAULT_MODEL if DEFAULT_MODEL in registry else list(registry.keys())[0]

    config = registry[model_key]
    log.info(f"Using AI Model: {config['name']} ({config['model_id']})")

    ai_input = build_ai_messages(
        model_type=config["type"],
        schema_text=ddl_text,
        question=question,
        history=history,
        knowledge=knowledge,
        db_type=db_type
    )

    # 根据返回类型决定使用 completions 还是 chat completions 端点
    if isinstance(ai_input, dict) and ai_input.get("is_completion"):
        # 微调模型：使用 /v1/completions 端点，直接发送格式化的 prompt
        # 这样可以避免服务器应用错误的 chat template (如 ChatML)
        payload = {
            "model": config["model_id"],
            "prompt": ai_input["prompt"],
            "temperature": 0.1,
            "stream": False,
            "max_tokens": 512,
            "stop": ["[/INST]", "[INST]", "<<SYS>>", "<</SYS>>", "\n\n\n"]
        }
        use_completion_api = True
    else:
        # 在线模型：使用 /v1/chat/completions 端点
        payload = {
            "model": config["model_id"],
            "messages": ai_input,
            "temperature": 0.1,
            "stream": False,
            "max_tokens": 512,
            "stop": ["User:", "Assistant:", "\n\n\n"]
        }
        use_completion_api = False

    headers = {
        "Authorization": f"Bearer {config['api_key']}",
        "Content-Type": "application/json"
    }

    try:
        # 根据模型类型选择 API 端点
        if use_completion_api:
            # 微调模型：使用 /v1/completions 端点
            # 将 /v1/chat/completions 替换为 /v1/completions
            api_url = config["api_url"].replace("/chat/completions", "/completions")
        else:
            api_url = config["api_url"]

        async with httpx.AsyncClient(timeout=300.0) as client:
            resp = await client.post(
                api_url,
                content=json.dumps(payload, ensure_ascii=False).encode("utf-8"), 
                headers=headers
            )
        resp.raise_for_status()
        raw = resp.json()
        
        content = ""
        if "choices" in raw and len(raw["choices"]) > 0:
            if use_completion_api:
                # completions 端点返回 text 字段
                content = raw["choices"][0].get("text", "")
            else:
                # chat completions 端点返回 message.content
                content = raw["choices"][0]["message"]["content"]
        
        return _clean_ai_response(content)

    except Exception as e:
        log.error("AI Call Error ({}): {}", model_key, e)
        return f"-- AI Service Error: {str(e)}"


# =========================================================
# 5. SQL 解析与执行
# =========================================================

def _parse_sql_type(sql_text: str) -> str:
    """解析 SQL 语句类型。"""
    sql_type = "UNKNOWN"
    try:
        if sql_text and not sql_text.startswith("--"):
            # 先清洗SQL文本，移除可能的前缀
            clean_sql = sql_text.strip()
            
            # 移除可能的前缀文本
            prefixes_to_remove = [
                "已生成sql语句：",
                "已生成SQL语句：", 
                "生成的SQL语句：",
                "SQL语句：",
                "查询语句："
            ]
            
            for prefix in prefixes_to_remove:
                if clean_sql.startswith(prefix):
                    clean_sql = clean_sql[len(prefix):].strip()
            
            # 使用sqlparse解析
            parsed = sqlparse.parse(clean_sql)
            if parsed:
                sql_type = parsed[0].get_type().upper()
                
            # 兜底逻辑：如果sqlparse无法识别，使用简单的关键字匹配
            if sql_type == "UNKNOWN":
                clean_upper = clean_sql.strip().upper()
                if clean_upper.startswith("SELECT"):
                    sql_type = "SELECT"
                elif clean_upper.startswith("INSERT"):
                    sql_type = "INSERT"
                elif clean_upper.startswith("UPDATE"):
                    sql_type = "UPDATE"
                elif clean_upper.startswith("DELETE"):
                    sql_type = "DELETE"
                elif clean_upper.startswith("CREATE"):
                    sql_type = "CREATE"
                elif clean_upper.startswith("DROP"):
                    sql_type = "DROP"
                elif clean_upper.startswith("ALTER"):
                    sql_type = "ALTER"
                elif clean_upper.startswith("TRUNCATE"):
                    sql_type = "TRUNCATE"
                    
    except Exception as e:
        log.warning("SQL parsing failed for: {}..., error: {}", sql_text[:100], e)
        
    return sql_type


def _is_meta_sql(sql_text: str) -> bool:
    """判断是否为元数据/错误 SQL。"""
    if not sql_text:
        return False
        
    sql_upper = sql_text.upper()
    
    # 检查是否包含错误关键字
    error_patterns = [
        "'CANCELED'",
        "'ERROR'", 
        "ERROR:",
        "CANNOT ANSWER",
        "无法回答",
        "CAN'T ANSWER",
        "UNABLE TO",
        "NOT SUPPORTED"
    ]
    
    return any(pattern in sql_upper for pattern in error_patterns)


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
        raise InvalidOperationException(message=f"不支持的数据库类型: {instance.db_type}")


# =========================================================
# 6. 消息持久化（独立事务）+ RAG 索引
# =========================================================

async def _save_user_message(
    db: AsyncSession,
    session_id: int,
    content: str
) -> MessageModel:
    """保存用户消息（独立事务），并异步触发向量索引。"""
    message = await crud_message.create_message(db, session_id, content, role="user")
    
    # 异步触发消息向量索引（不阻塞主流程）
    try:
        import asyncio
        asyncio.create_task(
            index_new_message(
                session_id=session_id,
                message_id=message.message_id,
                content=content,
                role="user"
            )
        )
    except Exception as e:
        # 索引失败不影响主流程
        log.warning(f"Failed to trigger message indexing: {e}")
    
    return message



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
    保存 AI 响应和执行结果（独立事务），并异步触发向量索引。
    """
    # 确保sql_text是干净的，不包含前缀
    clean_sql_text = sql_text
    prefixes_to_remove = [
        "已生成sql语句：",
        "已生成SQL语句：", 
        "生成的SQL语句：",
        "SQL语句：",
        "查询语句："
    ]
    
    for prefix in prefixes_to_remove:
        if clean_sql_text.startswith(prefix):
            clean_sql_text = clean_sql_text[len(prefix):].strip()
    
    # 构建回复内容，确保只有一个前缀
    reply_content = f"已生成SQL语句：\n{clean_sql_text}"
    ai_message = await crud_message.create_message(db, session_id, reply_content, role="assistant")
    
    # 异步触发 AI 回复的向量索引
    try:
        import asyncio
        asyncio.create_task(
            index_new_message(
                session_id=session_id,
                message_id=ai_message.message_id,
                content=reply_content,
                role="assistant"
            )
        )
    except Exception as e:
        log.warning(f"Failed to trigger AI response indexing: {e}")
    
    if requires_confirm:
        ai_message.requires_confirmation = True
        db.add(ai_message)

    safe_data = jsonable_encoder(data)
    new_statement = AIGeneratedStatement(
        message_id=ai_message.message_id,
        sql_text=clean_sql_text,  # 存储干净的SQL文本
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
    
    # 解析模型（异步，从数据库获取配置）
    final_model_key, model_registry = await _resolve_model_key(db, selected_model, session_obj.current_model)
    await _update_session_model(db, session_obj, final_model_key)
    log.info("Session {} using model: {}", session_id, final_model_key)
    
    # 获取历史和领域知识（使用 RAG 检索优化）
    # RAG 优化已实现：
    #   1. 将历史消息向量化存储（Embedding）
    #   2. 根据当前 user_input 进行语义相似度检索
    #   3. 只召回与当前问题相关的历史对话（Top-K）
    #   4. 领域知识也通过向量检索获取相关条目
    
    # 尝试使用 RAG 检索，失败时降级为传统方式
    history_context = []
    knowledge_context = []
    
    try:
        # 使用 RAG 检索相关上下文
        rag_context = await retrieve_chat_context(
            query=user_input,
            project_id=project_id,
            session_id=session_id,
            history_top_k=5,
            knowledge_top_k=5
        )
        
        # 将 RAG 检索结果转换为兼容格式
        # 历史对话：从向量检索结果构建 MessageModel 兼容对象
        if rag_context.relevant_history:
            history_context = await _convert_rag_history_to_messages(
                db, rag_context.relevant_history
            )
        
        # 领域知识：从向量检索结果构建 DomainKnowledge 兼容对象  
        if rag_context.relevant_knowledge:
            knowledge_context = await _convert_rag_knowledge_to_domain(
                db, rag_context.relevant_knowledge
            )
        
        log.info(f"RAG retrieved {len(history_context)} history, {len(knowledge_context)} knowledge")
        
    except Exception as e:
        # RAG 检索失败，降级为传统方式
        log.warning(f"RAG retrieval failed, falling back to traditional method: {e}")
        history_context = await crud_message.get_recent_messages(db, session_id, limit=20)
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
    
    # 获取数据库类型
    db_type = None
    if instance_id:
        database_instance = await crud_database_instance.get(db, instance_id)
        if database_instance:
            db_type = database_instance.db_type

    # 提交事务1，释放数据库连接
    await db.commit()
    
    # 检查取消指令（需要持久化提示消息）
    if user_input.strip() in ["取消", "cancel", "Stop"]:
        return await _handle_cancel_response(db, session_id)
    
    # === 阶段2：调用 AI（事务外，长连接） ===
    sql_text = await call_ai_agent(
        ddl_text,
        user_input,
        history=history_context,
        knowledge=knowledge_context,
        model_key=final_model_key,
        model_registry=model_registry,
        db_type=db_type
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
        content=f"已生成SQL语句：\n{sql_text}",
        message_type=MessageType.ASSISTANT,
        sql_text=sql_text,
        sql_type=sql_type,
        requires_confirmation=requires_confirm,
        data=jsonable_encoder(data)
    )


async def _handle_cancel_response(db: AsyncSession, session_id: int) -> ChatResponse:
    """持久化并返回取消操作的响应。"""
    reply_content = "好的，已为您取消当前操作。"
    ai_message = await crud_message.create_message(db, session_id, reply_content, role="assistant")
    await db.commit()

    return ChatResponse(
        message_id=ai_message.message_id,
        content=reply_content,
        message_type=MessageType.ASSISTANT,
        sql_text=None,
        sql_type="ACTION_CANCEL",
        requires_confirmation=False,
        data=None
    )


async def cancel_message(
    db: AsyncSession,
    message_id: int,
    user_id: int
) -> ChatResponse:
    """
    取消需要确认的消息：
    - 权限校验（会话归属）
    - 将原消息标记为已确认（用于隐藏前端按钮）
    - 将其关联的语句执行状态标记为 failed
    - 更新原消息内容，附加取消提示（与 SQL 语句合并显示）
    """
    log.info(f"cancel_message called: message_id={message_id}, user_id={user_id}")
    
    # 获取消息与会话信息
    stmt = select(MessageModel).where(MessageModel.message_id == message_id)
    result = await db.execute(stmt)
    message = result.scalar_one_or_none()
    if not message:
        log.warning(f"Message not found: message_id={message_id}")
        raise ItemNotFoundException(message="消息未找到")

    # 权限校验：仅会话所属用户可操作
    await _verify_session_ownership(db, message.session_id, user_id)

    # 获取关联的 SQL 语句
    stmt_query = select(AIGeneratedStatement).where(AIGeneratedStatement.message_id == message_id)
    stmt_result = await db.execute(stmt_query)
    ai_statement = stmt_result.scalar_one_or_none()
    
    sql_text = ai_statement.sql_text if ai_statement else None
    sql_type = ai_statement.statement_type if ai_statement else "UNKNOWN"

    # 标记原消息为"已确认"（用于隐藏确认/取消按钮）
    message.user_confirmed = True
    # 更新原消息内容，附加取消提示
    message.content = f"{message.content}❌ 已取消执行"
    db.add(message)

    # 更新关联的语句执行状态为 failed（数据库约束只允许 pending/completed/failed）
    if ai_statement:
        await db.execute(
            update(AIGeneratedStatement)
            .where(AIGeneratedStatement.message_id == message_id)
            .values(execution_status="failed")
        )

    await db.commit()

    # 返回更新后的原消息（不再创建新消息）
    return ChatResponse(
        message_id=message.message_id,
        content=message.content,
        message_type=MessageType.ASSISTANT,
        sql_text=sql_text,
        sql_type=sql_type,
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
        log.error("SQL Execution Error: {}", str(e))
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
        raise ItemNotFoundException(message="消息未找到")

    stmt_session = select(SessionModel).where(SessionModel.session_id == message.session_id)
    result_session = await db.execute(stmt_session)
    session_obj = result_session.scalar_one_or_none()
    if not session_obj:
        raise ItemNotFoundException(message="Session not found")

    stmt_project = select(ProjectModel).where(ProjectModel.project_id == session_obj.project_id)
    result_project = await db.execute(stmt_project)
    project = result_project.scalar_one_or_none()
    if not project:
        raise ItemNotFoundException(message="项目未找到")

    return message, session_obj, project


def _validate_confirmation(message: MessageModel, project: ProjectModel, user_id: int) -> None:
    """验证确认操作的合法性。"""
    if project.user_id != user_id:
        raise ForbiddenException(message="访问拒绝")
    if not message.requires_confirmation:
        raise InvalidOperationException(message="此消息不需要确认")
    if message.user_confirmed:
        raise InvalidOperationException(message="已确认/执行")


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
    original_message_id: int,
    error: Exception
) -> ChatResponse:
    """处理执行错误并返回错误响应，不创建新消息。"""
    # 优先获取 detail，因为 BusinessException/AppException 的 message 可能是类属性默认值"内部错误"
    error_msg = str(error)
    if hasattr(error, 'detail') and error.detail:
        error_msg = str(error.detail)
    elif hasattr(error, 'message') and error.message and error.message != "内部错误":
        error_msg = str(error.message)
    
    # 提供更友好的错误信息
    friendly_msg = _get_friendly_error_message(error_msg)
    content = f"❌ 执行失败：\n{friendly_msg}"
    
    return ChatResponse(
        message_id=original_message_id,  # 使用原始消息ID
        content=content,
        message_type=MessageType.ASSISTANT,
        sql_text=None,
        sql_type="ERROR",
        requires_confirmation=False,
        data=None
    )


def _get_friendly_error_message(error_msg: str) -> str:
    """将技术错误信息转换为用户友好的错误信息。"""
    error_lower = error_msg.lower()
    
    # 常见数据库错误的友好提示
    if "duplicate entry" in error_lower or "unique constraint" in error_lower:
        return "数据重复（违反唯一约束）。\n详细信息: " + error_msg
    elif "doesn't have a default value" in error_lower:
        return "必填字段缺失（字段没有默认值且未提供值，可能是主键未设置AUTO_INCREMENT）。\n详细信息: " + error_msg
    elif "cannot be null" in error_lower:
        return "字段不能为空。\n详细信息: " + error_msg
    elif "can't specify target table" in error_lower and "update in from clause" in error_lower:
        return "MySQL限制：INSERT/UPDATE语句中不能直接从同一张表SELECT。\n详细信息: " + error_msg
    elif "foreign key constraint" in error_lower:
        return "外键约束错误，请检查关联数据是否存在。\n详细信息: " + error_msg
    elif "table doesn't exist" in error_lower or "no such table" in error_lower:
        return "表不存在，请检查表名是否正确。\n详细信息: " + error_msg
    elif ("column" in error_lower and "doesn't exist" in error_lower) or "unknown column" in error_lower:
        return "列不存在，请检查列名是否正确。\n详细信息: " + error_msg
    elif "syntax error" in error_lower:
        return "SQL语法错误，请检查SQL语句。\n详细信息: " + error_msg
    elif "access denied" in error_lower or "permission denied" in error_lower:
        return "权限不足，无法执行此操作。\n详细信息: " + error_msg
    elif "data too long" in error_lower:
        return "数据过长，超出字段长度限制。\n详细信息: " + error_msg
    elif "incorrect" in error_lower and "value" in error_lower:
        return "数据类型或格式不正确。\n详细信息: " + error_msg
    else:
        # 对于未枚举的错误，仍然返回原始错误信息，而不是"内部错误"
        return "执行失败。\n详细信息: " + error_msg


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
        
        log.info("User {} executed DML and persisted results.", user_id)
        
    except Exception as e:
        log.error("Execution failed: {}", e)
        return await _handle_execution_error(db, message_id, e)

    return ChatResponse(
        message_id=message.message_id,
        content=message.content,
        message_type=MessageType.ASSISTANT,
        sql_text=sql_text,
        sql_type="DML_EXECUTED",
        requires_confirmation=False,
        data=execute_res
    )

"""
聊天 API 端点。

处理用户发送消息、获取历史记录，以及与 AI 模型的交互逻辑。
"""

import sqlparse
from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Any

# 1. 导入核心工具
from core.log import log
from service.chat_service import process_chat, confirm_and_execute_sql
from crud.crud_message import crud_message

# 3. 导入 Schema
from schema.chat import ChatResponse, ChatRequest, MessageType
from schema.user import UserMe
from api.v1.deps import get_current_active_user, get_db

router = APIRouter()

# src/backend/app/api/v1/endpoints/chat.py

def _format_history_response(raw_messages: List[Any]) -> List[ChatResponse]:
    """格式化消息历史，支持从持久化表获取 SQL 和结果集"""
    clean_history = []
    for msg in raw_messages:
        sql_text = None
        sql_type = "UNKNOWN"
        data = None # 新增：用于存储查询结果快照
        
        # 1. 优先从持久化模型 (AiGeneratedStatement) 获取元数据
        if hasattr(msg, 'ai_statement') and msg.ai_statement:
            # 假设一条消息对应一条 SQL 语句
            stmt = msg.ai_statement[0] if isinstance(msg.ai_statement, list) else msg.ai_statement
            if stmt:
                sql_text = getattr(stmt, 'sql_text', None)
                sql_type = getattr(stmt, 'statement_type', "UNKNOWN")
                # 【核心修改】从数据库中取出之前存好的 JSON 结果快照
                data = getattr(stmt, 'execution_result', None)

        # 2. 兜底解析逻辑（用于处理旧数据或未持久化的数据）
        msg_type = MessageType.ASSISTANT if getattr(msg, 'role', '') == "assistant" else MessageType.USER
        if msg_type == MessageType.ASSISTANT and not sql_text and msg.content:
            # ... 原有的正则或字符串切分逻辑保持不变 ...
            pass

        requires_conf = sql_type in ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE"]
        if getattr(msg, 'user_confirmed', False): 
            requires_conf = False

        clean_history.append(ChatResponse(
            message_id=msg.message_id if hasattr(msg, 'message_id') else msg.id,
            content=msg.content,
            message_type=msg_type,
            sql_text=sql_text,
            sql_type=sql_type,
            requires_confirmation=requires_conf,
            data=data # 现在 data 能够被正确返回给前端了
        ))
    return clean_history

@router.post("/sessions/{session_id}/messages", response_model=ChatResponse)
async def send_message(
    session_id: int = Path(...),
    chat_request: ChatRequest = None,
    db: AsyncSession = Depends(get_db),
    current_user: UserMe = Depends(get_current_active_user)
):
    """
    发送消息给 AI，并获取 SQL 生成结果。

    Args:
        session_id (int): 会话 ID。
        chat_request (ChatRequest): 聊天请求体。
        db (AsyncSession): 数据库会话。
        current_user (UserMe): 当前登录用户。

    Returns:
        ChatResponse: AI 响应结果。

    Raises:
        HTTPException: 内部错误(500)。
    """
    try:
        return await process_chat(
            db=db, session_id=session_id, user_input=chat_request.content,
            user_id=current_user.user_id, selected_model=chat_request.model 
        )
    except Exception as e:
        # 安全的日志记录方式
        log.error("Chat Error: {}", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error processing chat")

@router.get("/sessions/{session_id}/messages", response_model=List[ChatResponse])
async def get_history(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserMe = Depends(get_current_active_user)
):
    """
    获取会话历史消息。

    Args:
        session_id (int): 会话 ID。
        db (AsyncSession): 数据库会话。
        current_user (UserMe): 当前登录用户。

    Returns:
        List[ChatResponse]: 历史消息列表。

    Raises:
        HTTPException: 获取失败(500)。
    """
    try:
        raw_messages = await crud_message.get_recent_messages(db, session_id, limit=50)
        return _format_history_response(raw_messages)
    except Exception as e:
        log.error("History Error: {}", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve history")

@router.post("/messages/{message_id}/confirm", response_model=ChatResponse)
async def confirm_message_execution(
    message_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserMe = Depends(get_current_active_user)
):
    try:
        log.info(f"User {current_user.user_id} confirming message {message_id}")
        return await confirm_and_execute_sql(db, message_id, current_user.user_id)
    except HTTPException as he: raise he
    except Exception as e:
        # ✅ 修复：安全的日志记录方式
        log.error("Confirm Error: {}", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Execution failed: {str(e)}")
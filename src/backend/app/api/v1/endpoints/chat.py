"""
聊天 API 端点。

处理用户发送消息、获取历史记录，以及与 AI 模型的交互逻辑。
"""

import sqlparse
from fastapi import APIRouter, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Any

# 1. 导入核心工具
from core.log import log
from service.chat_service import process_chat, confirm_and_execute_sql
from crud.crud_message import crud_message
from core.exceptions import ItemNotFoundException

# 3. 导入 Schema
from schema.chat import ChatResponse, ChatRequest, MessageType
from schema.user import UserMe
from schema.unified_response import UnifiedResponse
from api.v1.deps import get_current_active_user, get_db

router = APIRouter()

# backend/app/api/v1/endpoints/chat.py

# backend/app/api/v1/endpoints/chat.py

def _format_history_response(raw_messages: List[Any]) -> List[ChatResponse]:
    clean_history = []
    for msg in raw_messages:
        # 1. 直接获取在 CRUD 中挂载好的持久化数据
        # 我们不再依赖 ai_statement，而是直接拿映射好的值
        sql_text = getattr(msg, 'sql_text', None)
        sql_type = getattr(msg, 'sql_type', 'UNKNOWN')
        data = getattr(msg, 'data', None) # <--- 获取持久化结果

        msg_type = MessageType.ASSISTANT if msg.message_type == "assistant" else MessageType.USER

        # 2. 如果 SQL 信息还没挂载上（比如某些异常情况），再尝试兜底解析
        if msg_type == MessageType.ASSISTANT and not sql_text and msg.content:
            try:
                # 你的原始兜底逻辑保持不变，但增加安全性
                content = msg.content
                if "已生成查询语句" in content:
                    sql_text = content.split("：")[-1].strip()
            except: pass

        requires_conf = sql_type in ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE"]
        if msg.user_confirmed: requires_conf = False

        # 3. 核心修复：把 data 传进去！
        clean_history.append(ChatResponse(
            message_id=msg.message_id,
            content=msg.content, 
            message_type=msg_type, 
            sql_text=sql_text, 
            sql_type=sql_type,
            requires_confirmation=requires_conf, 
            data=data  # <--- 修改这里：不再是 None，而是 msg.data
        ))
    return clean_history

@router.post("/sessions/{session_id}/messages", response_model=UnifiedResponse[ChatResponse])
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
        UnifiedResponse[ChatResponse]: AI 响应结果。
    """
    result = await process_chat(
        db=db, session_id=session_id, user_input=chat_request.content,
        user_id=current_user.user_id, selected_model=chat_request.model 
    )
    return UnifiedResponse.success(data=result, message="消息处理成功")

@router.get("/sessions/{session_id}/messages", response_model=UnifiedResponse[List[ChatResponse]])
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
        UnifiedResponse[List[ChatResponse]]: 历史消息列表。
    """
    raw_messages = await crud_message.get_recent_messages(db, session_id, limit=50)
    result = _format_history_response(raw_messages)
    return UnifiedResponse.success(data=result, message="获取历史消息成功")

@router.post("/messages/{message_id}/confirm", response_model=UnifiedResponse[ChatResponse])
async def confirm_message_execution(
    message_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserMe = Depends(get_current_active_user)
):
    log.info("User {} confirming message {}", current_user.user_id, message_id)
    result = await confirm_and_execute_sql(db, message_id, current_user.user_id)
    
    # 根据执行结果返回不同的消息
    if result.sql_type == "ERROR":
        return UnifiedResponse.success(data=result, message="SQL 执行失败")
    else:
        return UnifiedResponse.success(data=result, message="SQL 执行成功")
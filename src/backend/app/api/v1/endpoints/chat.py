"""
聊天 API 端点。
"""

import sqlparse
from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Any

from core.log import log
from service.chat_service import process_chat, confirm_and_execute_sql
from crud.crud_message import crud_message
from schema.chat import ChatResponse, ChatRequest, MessageType
from schema.user import UserMe
from api.v1.deps import get_current_active_user, get_db

router = APIRouter()

def _format_history_response(raw_messages: List[Any]) -> List[ChatResponse]:
    """格式化消息历史，包含兜底 SQL 解析"""
    clean_history = []
    for msg in raw_messages:
        sql_text = None
        sql_type = "UNKNOWN"
        
        # 1. 尝试从数据库元数据获取
        if msg.ai_statement:
            stmt = msg.ai_statement[0] if isinstance(msg.ai_statement, list) and len(msg.ai_statement) > 0 else msg.ai_statement
            if stmt and hasattr(stmt, 'sql_text'):
                sql_text = stmt.sql_text
                sql_type = stmt.statement_type

        # 2. 兜底解析
        msg_type = MessageType.ASSISTANT if hasattr(msg, 'message_type') and msg.message_type == "assistant" else MessageType.USER
        if msg_type == MessageType.ASSISTANT and not sql_text and msg.content:
            content = msg.content
            if "已生成查询语句" in content:
                content = content.split("：")[-1].strip()
            clean = content.replace("```sql", "").replace("```", "").strip()
            try:
                parsed = sqlparse.parse(clean)
                if parsed and parsed[0].get_type() != "UNKNOWN":
                    sql_text = clean
                    sql_type = parsed[0].get_type().upper()
            except: pass

        requires_conf = sql_type in ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE"]
        if msg.user_confirmed: requires_conf = False

        clean_history.append(ChatResponse(
            message_id=msg.message_id if hasattr(msg, 'message_id') else msg.id,
            content=msg.content, message_type=msg_type, sql_text=sql_text, sql_type=sql_type,
            requires_confirmation=requires_conf, data=None 
        ))
    return clean_history

@router.post("/sessions/{session_id}/messages", response_model=ChatResponse)
async def send_message(
    session_id: int = Path(...),
    chat_request: ChatRequest = None,
    db: AsyncSession = Depends(get_db),
    current_user: UserMe = Depends(get_current_active_user)
):
    try:
        return await process_chat(
            db=db, session_id=session_id, user_input=chat_request.content,
            user_id=current_user.user_id, selected_model=chat_request.model 
        )
    except Exception as e:
        # ✅ 修复：安全的日志记录方式
        log.error("Chat Error: {}", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error processing chat")

@router.get("/sessions/{session_id}/messages", response_model=List[ChatResponse])
async def get_history(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserMe = Depends(get_current_active_user)
):
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
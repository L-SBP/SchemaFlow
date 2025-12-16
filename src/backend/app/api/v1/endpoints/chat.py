"""
聊天 API 端点。

处理用户发送消息、获取历史记录，以及与 AI 模型的交互逻辑。
"""

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Any

# 1. 导入核心工具
from core.log import log

# 2. 导入 Service 和 CRUD
from service.chat_service import process_chat
from crud.crud_message import crud_message

# 3. 导入 Schema
from schema.chat import ChatResponse, ChatRequest, MessageType
from schema.user import UserMe  # 【重要】导入 UserMe Schema，因为鉴权返回的是这个

# 4. 导入依赖 (使用项目现有的统一依赖)
# get_db 通常在 core.deps 或 api.v1.deps 都有，这里统一从 api.v1.deps 拿
from api.v1.deps import get_current_active_user, get_db

router = APIRouter()

# --- 辅助函数：将数据库消息模型转换为 API 响应模型 ---
def _format_history_response(raw_messages: List[Any]) -> List[ChatResponse]:
    """
    格式化消息历史，提取 SQL 信息。

    Args:
        raw_messages (List[Any]): 原始消息列表。

    Returns:
        List[ChatResponse]: 格式化后的响应列表。
    """
    clean_history = []
    for msg in raw_messages:
        sql_text = None
        sql_type = "UNKNOWN"
        requires_confirmation = False
        
        # 处理 AI 生成的 SQL 语句
        if msg.ai_statement:
            # 兼容列表或单对象，取第一个核心 SQL
            stmt = msg.ai_statement[0] if isinstance(msg.ai_statement, list) and len(msg.ai_statement) > 0 else msg.ai_statement
            
            if stmt and hasattr(stmt, 'sql_text'):
                sql_text = stmt.sql_text
                sql_type = stmt.statement_type
                # 判断是否需要确认
                requires_confirmation = sql_type in ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER"]

        # 确定消息类型
        message_type = MessageType.USER
        if hasattr(msg, 'message_type') and msg.message_type == "assistant":
            message_type = MessageType.ASSISTANT

        # 构造响应对象
        response_item = ChatResponse(
            message_id=msg.message_id if hasattr(msg, 'message_id') else msg.id,
            content=msg.content,
            message_type=message_type,
            sql_text=sql_text,
            sql_type=sql_type,
            requires_confirmation=requires_confirmation,
            data=None 
        )
        clean_history.append(response_item)
    return clean_history


# --- 核心接口：发送自然语言消息 ---
@router.post("/sessions/{session_id}/messages", response_model=ChatResponse)
async def send_message(
    session_id: int = Path(..., description="会话ID"),
    chat_request: ChatRequest = None,
    db: AsyncSession = Depends(get_db),
    # 【核心修改】：使用 get_current_active_user
    # 注意：这里的类型注解是 UserMe (Pydantic Schema)，不是 UserAccount (ORM)
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
        # UserMe Schema 里也有 user_id 字段，可以直接用
        user_id = current_user.user_id
        
        log.info(f"User {user_id} sending message in session {session_id}")

        response = await process_chat(
            db=db, 
            session_id=session_id, 
            user_input=chat_request.content,
            user_id=user_id,             # 传入真实用户ID
            selected_model=chat_request.model 
        )
        return response
        
    except Exception as e:
        log.error(f"Chat Error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error processing chat")


# --- 辅助接口：获取历史消息 ---
@router.get("/sessions/{session_id}/messages", response_model=List[ChatResponse])
async def get_history(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    # 【核心修改】：统一鉴权，防止越权查看
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
        # TODO: 在 Service 层建议增加检查：session_id 是否属于 current_user.user_id
        
        # 1. 查数据库
        raw_messages = await crud_message.get_recent_messages(db, session_id, limit=50)
        
        # 2. 调用辅助函数转换数据
        return _format_history_response(raw_messages)
        
    except Exception as e:
        log.error(f"History Error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve history")
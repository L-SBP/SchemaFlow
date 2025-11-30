from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

# 1. 导入数据库和安全依赖
from core.deps import get_db
from api.v1 import deps  # 用于获取当前登录用户

# 2. 导入 Service 和 CRUD
from service.chat_service import process_chat
from crud.crud_message import crud_message
from models.user_account import UserAccount

# 3. 导入 Schema
from schema.chat import ChatResponse, ChatRequest, MessageType

router = APIRouter()

# --- 核心接口：发送自然语言消息 ---
@router.post("/sessions/{session_id}/messages", response_model=ChatResponse)
async def send_message(
    session_id: int = Path(..., description="会话ID"),
    chat_request: ChatRequest = None,
    db: AsyncSession = Depends(get_db)
):
    try:
        # 2. 我们假装是 1 号用户在操作
        # (只要你的数据库里有 project 和 session 数据就行，user_id 此时只是个数字)
        mock_user_id = 1 
        
        response = await process_chat(
            db=db, 
            session_id=session_id, 
            user_input=chat_request.content,
            user_id=mock_user_id # 把原来的 current_user.user_id 换成这个
        )
        return response
        
    except Exception as e:
        print(f"Chat Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# --- 辅助接口：获取历史消息 (升级版) ---
@router.get("/sessions/{session_id}/messages", response_model=List[ChatResponse])
async def get_history(
    session_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    获取会话历史消息，并格式化为前端统一的结构
    """
    try:
        # 1. 查数据库 (包含了关联的 AI Statement)
        raw_messages = await crud_message.get_recent_messages(db, session_id, limit=50)
        
        # 2. 数据转换 (Model -> Schema)
        clean_history = []
        for msg in raw_messages:
            # 提取 SQL 信息 (如果有的话)
            sql_text = None
            sql_type = "UNKNOWN"
            requires_confirmation = False
            
            # 检查是否有关联的 AI 生成语句
            if msg.ai_statement:
                # 我们取第一条 SQL (假设一次对话生成一个核心 SQL)
                # 兼容列表或单对象的情况
                stmt = msg.ai_statement[0] if isinstance(msg.ai_statement, list) and len(msg.ai_statement) > 0 else msg.ai_statement
                
                # 双重保险，防止空对象
                if stmt and hasattr(stmt, 'sql_text'):
                    sql_text = stmt.sql_text
                    sql_type = stmt.statement_type
                    # 根据 SQL 类型判断是否需要确认
                    requires_confirmation = sql_type in ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER"]

            # 3. 确定消息类型 - 使用正确的字段名 message_type
            # 根据数据库字段 message_type 来判断角色
            if hasattr(msg, 'message_type'):
                if msg.message_type == "user":
                    message_type = MessageType.USER
                else:
                    message_type = MessageType.ASSISTANT
            else:
                # 如果没有 message_type 字段，使用默认值
                message_type = MessageType.USER

            # 4. 构造统一的响应结构
            response_item = ChatResponse(
                message_id=msg.message_id if hasattr(msg, 'message_id') else msg.id,
                content=msg.content,  # 消息内容（用户提问或AI回复）
                message_type=message_type,  # 区分用户消息和AI消息
                sql_text=sql_text,         # 成功回显 SQL！
                sql_type=sql_type,
                requires_confirmation=requires_confirmation,
                data=None # 历史记录暂时不带查询结果数据，避免传输太慢
            )
            clean_history.append(response_item)
            
        return clean_history
        
    except Exception as e:
        print(f"History Error: {e}")
        # 打印详细错误栈，方便调试
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
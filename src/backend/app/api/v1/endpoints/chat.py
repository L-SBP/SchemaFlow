from fastapi import APIRouter, HTTPException
from typing import List

from src.backend.app.ai.chat.schemas import ChatRequest, ChatResponse
from src.backend.app.ai.chat.service import ChatService
from src.backend.app.core.database import get_mock_db

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat_with_ai(request: ChatRequest):
    """
    处理用户消息，生成AI响应（模拟版本）
    
    - **session_id**: 会话ID
    - **message**: 用户输入的自然语言消息  
    - **project_id**: 项目ID
    """
    try:
        # 使用模拟数据库
        mock_db = await get_mock_db()
        chat_service = ChatService(mock_db)
        
        result = await chat_service.process_user_message(
            request.message,
            request.session_id,
            request.project_id
        )
        
        return ChatResponse(**result)
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"处理消息失败: {str(e)}"
        )

@router.get("/sessions/{session_id}/messages")
async def get_session_messages(session_id: int):
    """
    获取指定会话的消息历史（模拟版本）
    """
    try:
        # 返回模拟数据
        return {
            "session_id": session_id,
            "messages": [
                {
                    "message_id": 1,
                    "message_type": "user", 
                    "content": "查询所有用户",
                    "created_at": "2024-01-01T10:00:00",
                    "requires_confirmation": False,
                    "user_confirmed": None
                },
                {
                    "message_id": 2,
                    "message_type": "assistant",
                    "content": "已生成查询SQL",
                    "created_at": "2024-01-01T10:00:01", 
                    "requires_confirmation": False,
                    "user_confirmed": None
                }
            ],
            "total_count": 2,
            "note": "这是模拟数据，数据库配置完成后将返回真实数据"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取消息历史失败: {str(e)}"
        )
from typing import Any, List
from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1 import deps
# 导入你现有的 crud 对象
from crud.crud_message import crud_message
# 导入 Schema，用于数据验证和返回格式化
from schema.message import MessageResponse 

router = APIRouter()

# 获取特定会话的历史消息
@router.get("/", response_model=List[MessageResponse], summary="获取会话消息历史")
async def read_messages(
    db: AsyncSession = Depends(deps.get_db),
    session_id: int = Query(..., description="会话ID"),
    limit: int = 50, # 你的 CRUD 支持 limit
) -> Any:
    """
    根据 session_id 获取该会话的消息历史记录。
    这里调用的是你 crud_message.py 中的 get_recent_messages 方法。
    """
    messages = await crud_message.get_recent_messages(
        db=db, session_id=session_id, limit=limit
    )
    return messages
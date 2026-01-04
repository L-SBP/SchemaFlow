"""
消息记录 Schema。

本模块定义了历史消息记录的查询和展示模型。
注意：实时聊天交互使用 `chat.py` 中的模型，此处主要用于历史记录回显。
"""

# backend/app/schema/message.py

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

# 消息的基础字段
class MessageBase(BaseModel):
    """
    消息基础 Schema。

    Attributes:
        message_type (str): 消息类型 (user, assistant, system)。
        content (str): 消息内容。
        requires_confirmation (bool): 是否需要用户确认。
        user_confirmed (Optional[bool]): 用户确认状态。
    """
    message_type: str = Field(..., description="消息类型: user, assistant, system")
    content: str = Field(..., description="消息内容")
    requires_confirmation: bool = Field(False, description="是否需要用户确认")
    user_confirmed: Optional[bool] = Field(None, description="用户确认状态")

# 创建消息时的参数
class MessageCreate(MessageBase):
    """
    创建消息请求 Schema。

    Attributes:
        session_id (int): 所属会话 ID。
    """
    session_id: int = Field(..., description="所属会话ID")

# API 返回的完整消息模型
class MessageResponse(MessageBase):
    """
    消息响应 Schema。

    Attributes:
        message_id (int): 消息 ID。
        session_id (int): 所属会话 ID。
        created_at (datetime): 创建时间。
    """
    message_id: int
    session_id: int
    created_at: datetime

    class Config:
        from_attributes = True
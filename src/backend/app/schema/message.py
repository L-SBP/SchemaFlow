from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

# 消息的基础字段
class MessageBase(BaseModel):
    message_type: str = Field(..., description="消息类型: user, assistant, system")
    content: str = Field(..., description="消息内容")
    requires_confirmation: bool = Field(False, description="是否需要用户确认")
    user_confirmed: Optional[bool] = Field(None, description="用户确认状态")

# 创建消息时的参数
class MessageCreate(MessageBase):
    session_id: int = Field(..., description="所属会话ID")

# API 返回的完整消息模型
class MessageResponse(MessageBase):
    message_id: int
    session_id: int
    created_at: datetime

    class Config:
        from_attributes = True
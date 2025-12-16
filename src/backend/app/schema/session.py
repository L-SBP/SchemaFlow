"""
会话管理 Schema。

本模块定义了聊天会话的创建、重命名、查询及响应模型。
"""

# backend/app/schema/session.py

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

# 基础 Schema，包含共享字段
class SessionBase(BaseModel):
    """
    会话基础 Schema。

    Attributes:
        session_name (Optional[str]): 会话名称。
    """
    session_name: Optional[str] = Field(default="New Session", description="会话名称")

# 创建会话时的请求模型
class SessionCreate(SessionBase):
    """
    创建会话请求 Schema。

    Attributes:
        project_id (int): 关联的项目 ID。
    """
    project_id: int = Field(..., description="关联的项目ID")

# 更新会话时的请求模型
class SessionUpdate(SessionBase):
    """
    更新会话请求 Schema。

    Attributes:
        session_name (Optional[str]): 会话名称。
    """
    session_name: Optional[str] = None
    # last_activity 通常由后端自动维护，不通过 API 直接修改

# API 返回的响应模型
class SessionResponse(SessionBase):
    """
    会话响应 Schema。

    Attributes:
        session_id (int): 会话 ID。
        project_id (int): 关联的项目 ID。
        created_at (datetime): 创建时间。
        last_activity (Optional[datetime]): 最后活动时间。
    """
    session_id: int
    project_id: int
    created_at: datetime
    last_activity: Optional[datetime]

    class Config:
        from_attributes = True  # 允许从 ORM 对象读取数据 (Pydantic V2 使用 model_config)
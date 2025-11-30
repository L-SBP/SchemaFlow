from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

# 基础 Schema，包含共享字段
class SessionBase(BaseModel):
    session_name: Optional[str] = Field(default="New Session", description="会话名称")

# 创建会话时的请求模型
class SessionCreate(SessionBase):
    project_id: int = Field(..., description="关联的项目ID")

# 更新会话时的请求模型
class SessionUpdate(SessionBase):
    session_name: Optional[str] = None
    # last_activity 通常由后端自动维护，不通过 API 直接修改

# API 返回的响应模型
class SessionResponse(SessionBase):
    session_id: int
    project_id: int
    created_at: datetime
    last_activity: Optional[datetime]

    class Config:
        from_attributes = True  # 允许从 ORM 对象读取数据 (Pydantic V2 使用 model_config)
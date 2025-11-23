from pydantic import BaseModel, Field
from typing import Literal
from datetime import datetime

# 创建会话
class SessionCreate(BaseModel):
    session_name: str = Field("New Session", max_length=50, description="会话名称")

# 会话信息
class SessionListOne(BaseModel):
    session_id: int
    session_name: str
    project_id: int
    created_at: datetime
    updated_at: datetime

#
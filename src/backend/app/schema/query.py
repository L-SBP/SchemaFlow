"""
查询分析 Schema。

本模块定义了用于自然语言查询、SQL 执行结果展示及图表推荐的数据模型。
"""

# backend/app/schema/query.py

from pydantic import BaseModel, Field, validator
from typing import Literal
from datetime import datetime

# 创建会话
class SessionCreate(BaseModel):
    """
    创建会话请求 Schema。

    Attributes:
        session_name (str): 会话名称 (默认 "New Session")。
    """
    session_name: str = Field("New Session", description="会话名称")
    
    @validator('session_name')
    def session_name_length(cls, v):
        if len(v) > 50:
            raise ValueError('会话名称长度不能超过50个字符')
        return v

# 会话信息
class SessionListOne(BaseModel):
    """
    会话列表单项 Schema。

    Attributes:
        session_id (int): 会话 ID。
        session_name (str): 会话名称。
        project_id (int): 项目 ID。
        created_at (datetime): 创建时间。
        updated_at (datetime): 更新时间。
    """
    session_id: int
    session_name: str
    project_id: int
    created_at: datetime
    updated_at: datetime

#
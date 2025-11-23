from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

# 聊天请求和响应
class ChatRequest(BaseModel):
    session_id: int
    message: str
    project_id: int

class ChatResponse(BaseModel):
    response: str
    sql_generated: Optional[str] = None
    requires_confirmation: bool = False
    statement_type: Optional[str] = None
    estimated_affected_rows: Optional[int] = None
    statement_id: Optional[int] = None

# 会话管理
class SessionCreate(BaseModel):
    project_id: int
    session_name: Optional[str] = "New Session"

class SessionResponse(BaseModel):
    session_id: int
    session_name: str
    created_at: datetime
    last_activity: Optional[datetime]

# 消息历史
class MessageResponse(BaseModel):
    message_id: int
    message_type: str
    content: str
    created_at: datetime
    requires_confirmation: bool
    user_confirmed: Optional[bool]

# AI生成的SQL语句
class SQLStatementResponse(BaseModel):
    statement_id: int
    sql_text: str
    statement_type: str
    execution_status: str
    created_at: datetime
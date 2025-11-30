from pydantic import BaseModel
from typing import List, Optional, Any, Dict
from enum import Enum

class MessageType(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"

# 1. 接收用户发送的消息
class ChatRequest(BaseModel):
    content: str  # 用户输入的自然语言内容

# 2. 返回给前端的 SQL 语句详情
class SQLStatement(BaseModel):
    statement_id: int
    sql_text: str
    type: str  # SELECT, INSERT, UPDATE 等
    result_summary: Optional[str] = None

# 3. 返回给前端的数据结果 (SELECT 结果)
class ExecutionResult(BaseModel):
    data: List[Dict[str, Any]]  # 具体的行数据
    data_summary: str           # AI 对数据的总结
    chart_type: Optional[str] = "table"

# 4. 响应体：包含完整的对话信息
class ChatResponse(BaseModel):
    message_id: int               # 消息ID，方便后续引用
    content: str                  # 消息内容（用户提问或AI回复）
    message_type: MessageType     # 区分是用户消息还是AI消息
    
    sql_text: Optional[str] = None  # 生成的 SQL，前端可以展示在代码块里
    sql_type: str = "UNKNOWN"       # SELECT / DELETE / UPDATE ...
    
    requires_confirmation: bool   # 核心字段：告诉前端要不要弹窗确认
    
    # 暂时预留 data 字段，等同学 C 做好执行逻辑后，这里填查询结果
    data: Optional[List[Dict[str, Any]]] = None
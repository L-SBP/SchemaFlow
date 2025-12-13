from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Any, Dict
from enum import Enum

# 定义消息类型枚举
class MessageType(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"  # 补充 system 类型，以防万一

# 1. 接收用户发送的消息 (Request DTO)
class ChatRequest(BaseModel):
    content: str = Field(..., min_length=1, description="用户输入的自然语言内容")
    # 允许前端指定模型，可选值建议与后端 Registry 保持一致，但为了灵活先用 str
    model: Optional[str] = Field(None, description="指定使用的AI模型ID，如 'xiyan-sql'")

# 2. 响应体：包含完整的对话信息 (Response DTO)
class ChatResponse(BaseModel):
    message_id: int = Field(..., description="消息ID")
    content: str = Field(..., description="消息内容")
    message_type: MessageType = Field(..., description="消息角色")
    
    # SQL 相关信息 (Flattened 扁平化设计，方便前端直接读取)
    sql_text: Optional[str] = Field(None, description="生成的 SQL 语句")
    sql_type: str = Field("UNKNOWN", description="SQL 类型: SELECT/INSERT/UPDATE...")
    
    requires_confirmation: bool = Field(False, description="是否需要用户确认执行")
    
    # 数据结果 (动态结构)
    # 对于动态表格数据，List[Dict] 是 Pydantic 中处理不确定列名的标准做法
    data: Optional[List[Dict[str, Any]]] = None 

    model_config = ConfigDict(from_attributes=True) # 支持从 ORM 对象读取
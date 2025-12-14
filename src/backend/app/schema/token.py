# src/backend/app/schema/token.py

from typing import Optional
from pydantic import BaseModel

class Token(BaseModel):
    """
    返回给前端的 Token 响应体
    """
    access_token: str
    token_type: str

class TokenPayload(BaseModel):
    """
    JWT 解析后的载荷数据
    """
    # sub (Subject) 是 JWT 标准字段，通常用来存用户 ID
    # 你的用户 ID 是 int 类型，所以这里定义为 Optional[int]
    sub: Optional[int] = None
# backend/app/schema/knowledge.py

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime

# --- 基础模型 ---
class KnowledgeBase(BaseModel):
    term: str = Field(..., description="业务术语", min_length=1, max_length=100)
    definition: str = Field(..., description="术语定义")
    examples: Optional[str] = Field(None, description="使用示例")

# --- 3.4.1 创建/更新请求 ---
class KnowledgeCreate(KnowledgeBase):
    pass

# 更新术语请求
class KnowledgeUpdate(KnowledgeBase):
    term: Optional[str] = Field(None, min_length=1, max_length=100)
    definition: Optional[str] = None
    examples: Optional[str] = None


# 批量删除请求
class BulkDeleteRequest(BaseModel):
    ids: List[int] = Field(..., description="要删除的知识条目ID列表")

# --- 3.4.1 / 3.4.2 响应对象 ---
class KnowledgeResponse(KnowledgeBase):
    knowledge_id: int
    project_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- 3.4.2 分页列表响应 ---
class PaginatedKnowledgeList(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[KnowledgeResponse]

    model_config = ConfigDict(from_attributes=True)

# --- 3.4.3 导入结果响应 ---
class ImportFailure(BaseModel):
    row: int
    error: str

class ImportResponse(BaseModel):
    imported_count: int
    failed_count: int
    failures: List[ImportFailure]

# --- 3.4.4 导出结果响应 ---
class ExportResponse(BaseModel):
    download_url: str
    expires_at: datetime
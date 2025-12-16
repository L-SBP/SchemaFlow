"""
领域知识 Schema。

本模块定义了业务术语（领域知识）的创建、查询和响应模型。
用于增强 AI 对特定行业术语的理解能力。
"""

# backend/app/schema/knowledge.py

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime

# --- 基础模型 ---
class KnowledgeBase(BaseModel):
    """
    知识库基础 Schema。

    Attributes:
        term (str): 业务术语。
        definition (str): 术语定义。
        examples (Optional[str]): 使用示例。
    """
    term: str = Field(..., description="业务术语", min_length=1, max_length=100)
    definition: str = Field(..., description="术语定义")
    examples: Optional[str] = Field(None, description="使用示例")

# --- 3.4.1 创建/更新请求 ---
class KnowledgeCreate(KnowledgeBase):
    """
    创建术语请求 Schema。
    """
    pass

# 更新术语请求
class KnowledgeUpdate(KnowledgeBase):
    """
    更新术语请求 Schema。

    Attributes:
        term (Optional[str]): 业务术语。
        definition (Optional[str]): 术语定义。
        examples (Optional[str]): 使用示例。
    """
    term: Optional[str] = Field(None, min_length=1, max_length=100)
    definition: Optional[str] = None
    examples: Optional[str] = None


# 批量删除请求
class BulkDeleteRequest(BaseModel):
    """
    批量删除术语请求 Schema。

    Attributes:
        ids (List[int]): 要删除的知识条目ID列表。
    """
    ids: List[int] = Field(..., description="要删除的知识条目ID列表")

# --- 3.4.1 / 3.4.2 响应对象 ---
class KnowledgeResponse(KnowledgeBase):
    """
    术语响应 Schema。

    Attributes:
        knowledge_id (int): 知识条目ID。
        project_id (int): 所属项目ID。
        created_at (datetime): 创建时间。
    """
    knowledge_id: int
    project_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- 3.4.2 分页列表响应 ---
class PaginatedKnowledgeList(BaseModel):
    """
    术语分页列表响应 Schema。

    Attributes:
        total (int): 总记录数。
        page (int): 当前页码。
        page_size (int): 每页数量。
        items (List[KnowledgeResponse]): 术语列表。
    """
    total: int
    page: int
    page_size: int
    items: List[KnowledgeResponse]

    model_config = ConfigDict(from_attributes=True)

# --- 3.4.3 导入结果响应 ---
class ImportFailure(BaseModel):
    """
    导入失败记录 Schema。

    Attributes:
        row (int): 失败行号。
        error (str): 错误信息。
    """
    row: int
    error: str

class ImportResponse(BaseModel):
    """
    导入结果响应 Schema。

    Attributes:
        imported_count (int): 成功导入数量。
        failed_count (int): 失败数量。
        failures (List[ImportFailure]): 失败记录列表。
    """
    imported_count: int
    failed_count: int
    failures: List[ImportFailure]

# --- 3.4.4 导出结果响应 ---
class ExportResponse(BaseModel):
    """
    导出结果响应 Schema。

    Attributes:
        download_url (str): 下载链接。
        expires_at (datetime): 链接过期时间。
    """
    download_url: str
    expires_at: datetime
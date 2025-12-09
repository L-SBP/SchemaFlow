# backend/app/schema/project.py

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Literal, List, Any,Dict
from datetime import datetime
from enum import Enum


# --- 1. 枚举定义 (严格匹配文档) ---

class ProjectStatusEnum(str, Enum):
    """3.2. 项目状态：initializing, active, deleted"""
    INITIALIZING = "initializing"
    ACTIVE = "active"  # <--- 修正：文档要求是 active
    DELETED = "deleted"


class CreationStageEnum(str, Enum):
    """3.2.2. 创建进度阶段"""
    INITIALIZING = "initializing"
    GENERATING_SCHEMA = "generating_schema"
    GENERATING_DDL = "generating_ddl"
    EXECUTING_DDL = "executing_ddl"
    COMPLETED = "completed"


# --- 2. 请求 DTOs ---

class ProjectCreate(BaseModel):
    """3.2.1 创建项目请求"""
    project_name: str = Field(..., min_length=1, max_length=50, description="项目名称")
    db_type: Literal['mysql', 'postgresql', 'sqlite'] = Field(..., description="数据库类型")
    description: str = Field(..., max_length=1000, description="项目描述")
    ai_model: Literal["gpt4", "deepseek", "chatgpt"] = Field("gpt4",description="用于生成Schema的AI模型")


class ProjectUpdate(BaseModel):
    """3.2.4 更新项目请求 (PATCH)"""
    project_name: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=500)
    # =========================================================
    # 新增：允许前端回传修改后的 Schema/DDL 进行保存
    # =========================================================
    schema_definition: Optional[Dict[str, Any]] = Field(
        None,
        description="前端修改后的DDL和Schema结构 {'ddl': '...', 'schema': '...'}"
    )


class DeleteConfirmationRequest(BaseModel):
    """3.2.5 确认删除请求"""
    confirmation_text: str = Field(..., pattern=r'^DELETE$', description="必须输入 DELETE")


# --- 3. 响应 DTOs ---

class ProjectAsyncResponse(BaseModel):
    """3.2.1 异步创建响应 (202 Accepted)"""
    project_id: int
    project_name: str
    # 使用 alias="status" 匹配前端期望的 {"status": "..."}
    project_status: ProjectStatusEnum = Field(..., alias="status")
    message: str = "项目创建请求已受理，正在初始化..."

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ProjectListOne(BaseModel):
    """3.2.3 列表单项"""
    project_id: int
    project_name: str
    description: Optional[str] = None
    project_status: ProjectStatusEnum
    updated_at: datetime
    db_type: str
    model_config = ConfigDict(from_attributes=True)


class PaginatedProjectList(BaseModel):
    """3.2.3 分页列表包装器"""
    total: int
    page: int
    page_size: int
    items: List[ProjectListOne]

    model_config = ConfigDict(from_attributes=True)


class ProjectDetailOut(ProjectListOne):
    """详情 DTO 内部结构"""
    created_at: datetime
    creation_stage: Optional[CreationStageEnum] = CreationStageEnum.INITIALIZING
    progress_percentage: Optional[int] = 0
    # 可以添加 analysis_result, ddl_result 等字段
    # =========================================================
    # 新增：将数据库中的 JSONB 字段返回给前端
    # =========================================================
    schema_definition: Optional[Dict[str, Any]] = Field(
        None,
        description="AI生成的包含 'schema' 和 'ddl' 的JSON对象"
    )

    model_config = ConfigDict(from_attributes=True)


class ProjectResponse(BaseModel):
    """3.2.2 / 3.2.4 单个项目包装器 {"data": ...}"""
    data: ProjectDetailOut

    model_config = ConfigDict(from_attributes=True)


class ConfirmationTokenResponse(BaseModel):
    """3.2.5 删除令牌响应"""
    confirmation_token: str
    expires_at: datetime
"""
项目管理 Schema。

本模块定义了项目的创建、配置更新、数据库连接信息及状态流转相关的模型。
"""

# backend/app/schema/project.py

from pydantic import BaseModel, Field, ConfigDict, validator
from typing import Optional, Literal, List, Any,Dict
from datetime import datetime
from enum import Enum


# --- 1. 枚举定义 ---
class ProjectStatusEnum(str, Enum):
    INITIALIZING = "initializing"          # 正在生成或等待确认
    PENDING_CONFIRMATION = "pending_confirmation" # (新增建议) 生成完毕，等待用户确认
    ACTIVE = "active"                      # 已部署
    DELETED = "deleted"


class CreationStageEnum(str, Enum):
    """3.2.2. 创建进度阶段"""
    INITIALIZING = "initializing"
    GENERATING_SCHEMA = "generating_schema"  # 正在生成 Schema
    SCHEMA_GENERATED = "schema_generated"  # Schema 生成完毕，等待用户确认
    GENERATING_DDL = "generating_ddl"  # 正在生成 DDL
    DDL_GENERATED = "ddl_generated"  # DDL 生成完毕，等待用户部署
    EXECUTING_DDL = "executing_ddl"  # 正在部署
    COMPLETED = "completed"  # 完成


# --- 2. 请求 DTOs ---

class ProjectCreate(BaseModel):
    """
    创建项目请求体。

    Attributes:
        project_name (str): 项目名称。
        db_type (Literal): 数据库类型（mysql、postgresql、sqlite）。
        description (str): 项目描述。
        ai_model (Literal): 用于生成Schema的AI模型。
    """
    project_name: str = Field(..., description="项目名称")
    db_type: Literal['mysql', 'postgresql', 'sqlite'] = Field(..., description="数据库类型")
    description: str = Field(..., description="项目描述")
    ai_model: Literal["gpt4", "deepseek", "chatgpt"] = Field("gpt4",description="用于生成Schema的AI模型")
    
    @validator('project_name')
    def project_name_length(cls, v):
        if not 1 <= len(v) <= 50:
            raise ValueError('项目名称长度必须在1到50个字符之间')
        return v
    
    @validator('description')
    def description_length(cls, v):
        if len(v) > 1000:
            raise ValueError('项目描述长度不能超过1000个字符')
        return v


class ProjectUpdate(BaseModel):
    """
    更新项目请求体（PATCH）。

    Attributes:
        project_name (Optional[str]): 项目名称。
        description (Optional[str]): 项目描述。
        schema_definition (Optional[Dict[str, Any]]): 前端修改后的DDL和Schema结构。
    """
    project_name: Optional[str] = Field(None, description="项目名称")
    description: Optional[str] = Field(None, description="项目描述")
    # =========================================================
    # 允许前端回传修改后的 Schema/DDL 进行保存
    # =========================================================
    schema_definition: Optional[Dict[str, Any]] = Field(
        None,
        description="前端修改后的DDL和Schema结构 {'ddl': '...', 'schema': '...'}"
    )
    ddl_statement: Optional[str] = None
    
    @validator('project_name')
    def project_name_length(cls, v):
        if v is not None and not 1 <= len(v) <= 50:
            raise ValueError('项目名称长度必须在1到50个字符之间')
        return v
    
    @validator('description')
    def description_length(cls, v):
        if v is not None and len(v) > 500:
            raise ValueError('项目描述长度不能超过500个字符')
        return v


class GenerateDDLRequest(BaseModel):
    """
    用户确认 Schema 后，请求生成 DDL 的参数。
    """
    confirmed_schema: str = Field(..., description="用户确认或修改后的 Schema 内容")
    # 如果用户在确认 Schema 阶段同时也微调了需求，可以传此参数更新项目描述，否则使用原描述
    requirements: Optional[str] = Field(None, description="可选：修正后的需求描述")


# --- ：部署请求 DTO ---
class ProjectDeployRequest(BaseModel):
    """
    用户确认并提交部署的请求体。

    Attributes:
        confirmed_ddl (str): 用户确认后的最终 DDL 语句。
        confirmed_schema (Optional[str]): 对应的 Schema 描述。
        use_smart_parse (bool): 是否使用后端的方言转换和拓扑排序。
    """
    confirmed_ddl: str = Field(..., description="用户确认后的最终 DDL 语句")
    confirmed_schema: Optional[str] = Field(None, description="对应的 Schema 描述")
    # --- 预留接口：控制是否使用后端的高级解析功能 ---
    use_smart_parse: bool = Field(
        False,
        description="是否使用后端的方言转换和拓扑排序。默认为True。未来如果AI生成的DDL足够完美，可设为False直接执行。"
    )


class DeleteConfirmationRequest(BaseModel):
    """3.2.5 确认删除请求"""
    confirmation_text: str = Field(..., description="必须输入 DELETE")
    
    @validator('confirmation_text')
    def confirmation_text_must_be_delete(cls, v):
        if v != 'DELETE':
            raise ValueError('必须输入 DELETE 以确认删除')
        return v


# --- 3. 响应 DTOs ---

class ProjectAsyncResponse(BaseModel):
    """
    异步创建项目的响应体 (202 Accepted)。

    Attributes:
        project_id (int): 项目 ID。
        project_name (str): 项目名称。
        project_status (ProjectStatusEnum): 项目状态。
        message (str): 响应消息。
    """
    project_id: int
    project_name: str
    # 使用 alias="status" 匹配前端期望的 {"status": "..."}
    project_status: ProjectStatusEnum = Field(..., alias="status")
    message: str = "项目创建请求已受理，正在初始化..."

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ProjectListOne(BaseModel):
    """
    项目列表单项。

    Attributes:
        project_id (int): 项目 ID。
        project_name (str): 项目名称。
        description (Optional[str]): 项目描述。
        project_status (ProjectStatusEnum): 项目状态。
        updated_at (datetime): 更新时间。
        db_type (str): 数据库类型。
    """
    project_id: int
    project_name: str
    description: Optional[str] = None
    project_status: ProjectStatusEnum
    updated_at: datetime
    db_type: str
    model_config = ConfigDict(from_attributes=True)


class PaginatedProjectList(BaseModel):
    """
    项目分页列表包装器。

    Attributes:
        total (int): 项目总数。
        page (int): 当前页码。
        page_size (int): 每页数量。
        items (List[ProjectListOne]): 项目列表。
    """
    total: int
    page: int
    page_size: int
    items: List[ProjectListOne]

    model_config = ConfigDict(from_attributes=True)


class ProjectDetailOut(ProjectListOne):
    """
    项目详情 DTO。

    Attributes:
        created_at (datetime): 创建时间。
        creation_stage (Optional[CreationStageEnum]): 创建进度阶段。
        schema_definition (Optional[Dict[str, Any]]): AI生成的包含 'schema' 和 'ddl' 的JSON对象。
    """
    created_at: datetime
    creation_stage: Optional[CreationStageEnum] = CreationStageEnum.INITIALIZING
    # 可以添加 analysis_result, ddl_result 等字段
    # =========================================================
    # 将数据库中的 JSONB 字段返回给前端
    # =========================================================
    schema_definition: Optional[Dict[str, Any]] = Field(
        None,
        description="AI生成的包含 'schema' 和 'ddl' 的JSON对象"
    )
    ddl_statement: Optional[str] = Field(None, description="DDL 语句文本")
    er_diagram_code: Optional[str] = Field(None, description="Mermaid ER图代码")
    model_config = ConfigDict(from_attributes=True)


# Removed ProjectResponse wrapper to avoid unnecessary nesting
# ProjectDetailOut is used directly in API responses


class ConfirmationTokenResponse(BaseModel):
    """
    删除令牌响应体。

    Attributes:
        confirmation_token (str): 删除令牌。
        expires_at (datetime): 令牌过期时间。
    """
    confirmation_token: str
    expires_at: datetime
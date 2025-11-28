from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Literal, List, Any
from datetime import datetime

# 创建项目
class ProjectCreate(BaseModel):
    project_name: str = Field(..., min_length=3, max_length=50, description="项目名称")
    db_type: str = Literal['mysql', 'postgressql', 'sqlite']
    description: str = Field(..., max_length=500, description="项目描述")

# 退出项目
class ProjectOut(BaseModel):
    project_id: int
    user_id: str
    instance_id: str
    project_name: str
    description: str = None
    project_status: Literal['activate', 'inactivate', 'deleted'] = 'activate'
    updated_at: datetime

# 获取项目列表
class ProjectListOne(BaseModel):
    project_id: int
    project_name: str
    project_status: Literal['activate', 'inactivate', 'deleted'] = 'activate'
    updated_at: datetime

# 获取项目详情
class ProjectDetail(ProjectListOne):
    description: str

# 项目搜索
class ProjectSearch(BaseModel):
    project_name: Optional[str] = None


class ProjectListResponse(BaseModel):
    data: List['ProjectListOne']

    # 启用 ORM 兼容 (可选，但推荐)
    model_config = ConfigDict(from_attributes=True)


class ProjectResponse(BaseModel):
    # 包装 ProjectDetail 类
    data: 'ProjectDetail'

    # 启用 ORM 兼容 (可选，但推荐)
    model_config = ConfigDict(from_attributes=True)


class ProjectAsyncResponse(BaseModel):
    """
    项目异步创建响应 DTO
    """
    project_id: int = Field(..., description="新创建项目的ID")
    project_name: str
    status: Literal['initializing', 'active', 'deleted'] = 'initializing'
    message: str = Field(..., description="请求受理状态描述")

    model_config = ConfigDict(from_attributes=True)


class PaginatedProjectList(BaseModel):
    """
    项目分页列表响应 DTO
    """
    total: int = Field(..., description="总记录数")
    page: int = Field(1, description="当前页码")
    page_size: int = Field(20, description="每页记录数")

    # 列表项使用 ProjectListOne DTO
    items: List['ProjectListOne']

    model_config = ConfigDict(from_attributes=True)


class ProjectUpdate(BaseModel):
    """
    用于 PATCH /projects/{project_id} 更新项目信息
    所有字段应为 Optional
    """
    project_name: Optional[str] = Field(None, min_length=3, max_length=50, description="项目名称")
    db_type: Optional[str] = Literal[None, 'mysql', 'postgressql', 'sqlite']
    description: Optional[str] = Field(None, max_length=500, description="项目描述")

    # 注意：如果你的 PATCH DTO 继承自 ProjectCreate，需要确保字段被正确覆盖为 Optional。
    # 这里我们直接定义一个独立的 PATCH DTO。

    # 如果需要处理 ORM 映射，通常也加上这个配置
    model_config = ConfigDict(from_attributes=True)


class DeleteConfirmationRequest(BaseModel):
    confirmation_text: str = Field(..., description="用户确认删除的文本，通常是 DELETE")


class ConfirmationTokenResponse(BaseModel):
    confirmation_token: str = Field(..., description="用于最终删除的确认令牌")
    expires_at: datetime = Field(..., description="令牌过期时间")

    # 启用 ORM 兼容 (如果 Service 返回的是 ORM/Dict)
    model_config = ConfigDict(from_attributes=True)
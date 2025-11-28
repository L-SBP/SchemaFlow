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



# backend/app/schema/admin.py

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Literal, Any
from datetime import datetime
from schema.user import UserMe  # 确保这里能导入 UserMe


# ----------------------------------------------------------------------
# 0. 通用分页基类
# ----------------------------------------------------------------------
class PaginatedResponseSchema(BaseModel):
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页记录数")

    model_config = ConfigDict(from_attributes=True)


# ----------------------------------------------------------------------
# 4.1. 用户管理 Schemas
# ----------------------------------------------------------------------

# 4.1.1. 列表单项 DTO
class AdminUserListItem(BaseModel):
    user_id: int
    username: str
    email: str
    status: Literal["normal", "suspended", "banned"]
    project_count: int = Field(0, description="该用户拥有的项目数量")
    max_databases: int = Field(10, description="该用户最大数据库额度")
    last_login_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# 4.1.1. 用户列表响应
class AdminUserListResponse(PaginatedResponseSchema):
    items: List[AdminUserListItem]


# 4.1.2. 修改用户状态 - Request
class AdminUpdateUserStatusRequest(BaseModel):
    status: Literal["normal", "banned", "suspended"]
    reason: str = Field(..., description="操作原因")


# 4.1.2. 修改用户状态 - Response (新增，解决 ImportError)
class AdminUpdateUserStatusResponse(BaseModel):
    user_id: int
    status: Literal["normal", "suspended", "banned"]
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# 4.1.3. 调整用户资源额度 - Request
class AdminUpdateUserQuotaRequest(BaseModel):
    max_databases: int = Field(..., gt=0, description="新的最大数据库额度")


# 4.1.3. 调整用户资源额度 - Response (新增，解决 ImportError)
class AdminUpdateUserQuotaResponse(BaseModel):
    user_id: int
    max_databases: int
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ----------------------------------------------------------------------
# 4.2. 公告管理 Schemas
# ----------------------------------------------------------------------

class AnnouncementCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    content: str
    status: Literal['draft', 'published'] = 'published'


class AnnouncementUpdateRequest(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    status: Optional[Literal["draft", "published", "unpublished", "expired"]] = None


class AnnouncementResponse(BaseModel):
    announcement_id: int
    title: str
    content: str
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None  # 允许为空

    model_config = ConfigDict(from_attributes=True)


# ----------------------------------------------------------------------
# 4.3. 管理员列表 & 4.4. 违规/统计 Schemas
# ----------------------------------------------------------------------

# 管理员列表单项
class AdminListItem(BaseModel):
    user_id: int
    username: str
    email: str
    last_login_at: Optional[datetime]
    is_online: bool = False

    model_config = ConfigDict(from_attributes=True)


# 管理员列表响应
class AdminListResponse(PaginatedResponseSchema):
    items: List[AdminListItem]


# 违规记录单项
class ViolationLogListItem(BaseModel):
    violation_id: int
    user_id: int
    username: str
    risk_level: str
    resolution_status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# 违规记录列表响应
class ViolationLogListResponse(PaginatedResponseSchema):
    items: List[ViolationLogListItem]


# 系统统计响应
class AdminStatsResponse(BaseModel):
    active_users_today: int
    total_projects: int
    query_count_today: int
    high_risk_operations_today: int
    system_health: Literal["good", "warning", "critical"]
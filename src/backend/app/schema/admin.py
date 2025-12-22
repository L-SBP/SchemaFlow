"""
管理员管理模块 Schema。

本模块定义了管理员进行用户管理、封禁、解封以及获取系统统计数据所需的 Pydantic 模型。
包含分页请求、封禁操作、解封审批及各类响应体结构。
"""

# backend/app/schema/admin.py

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Literal, Any
from datetime import datetime
from schema.user import UserMe  # 确保这里能导入 UserMe


# ----------------------------------------------------------------------
# 0. 通用分页基类
# ----------------------------------------------------------------------
class PaginatedResponseSchema(BaseModel):
    """
    通用分页响应基类。

    Attributes:
        total (int): 总记录数。
        page (int): 当前页码。
        page_size (int): 每页记录数。
    """
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页记录数")

    model_config = ConfigDict(from_attributes=True)


# ----------------------------------------------------------------------
# 4.1. 用户管理 Schemas
# ----------------------------------------------------------------------

# 4.1.1. 列表单项 DTO
class AdminUserListItem(BaseModel):
    """
    管理员视角的用户列表单项。

    Attributes:
        user_id (int): 用户 ID。
        username (str): 用户名。
        email (str): 邮箱。
        status (str): 用户状态。
        project_count (int): 该用户拥有的项目数量。
        max_databases (int): 该用户最大数据库额度。
        last_login_at (Optional[datetime]): 最后登录时间。
    """
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
    """
    用户列表响应 Schema。

    Attributes:
        items (List[AdminUserListItem]): 用户列表项。
    """
    items: List[AdminUserListItem]


# 4.1.2. 用户状态 - Request
class AdminUpdateUserStatusRequest(BaseModel):
    """
    修改用户状态请求 Schema。

    Attributes:
        status (str): 新状态。
        reason (str): 操作原因。
    """
    status: Literal["normal", "banned", "suspended"]
    reason: str = Field(..., description="操作原因")


# 4.1.2. 用户状态 - Response (新增，解决 ImportError)
class AdminUpdateUserStatusResponse(BaseModel):
    """
    修改用户状态响应 Schema。

    Attributes:
        user_id (int): 用户 ID。
        status (str): 更新后的状态。
        updated_at (datetime): 更新时间。
    """
    user_id: int
    status: Literal["normal", "suspended", "banned"]
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# 4.1.3. 调整用户资源额度 - Request
class AdminUpdateUserQuotaRequest(BaseModel):
    """
    调整用户资源额度请求 Schema。

    Attributes:
        max_databases (int): 新的最大数据库额度。
    """
    max_databases: int = Field(..., gt=0, description="新的最大数据库额度")


# 4.1.3. 调整用户资源额度 - Response (新增，解决 ImportError)
class AdminUpdateUserQuotaResponse(BaseModel):
    """
    调整用户资源额度响应 Schema。

    Attributes:
        user_id (int): 用户 ID。
        max_databases (int): 更新后的最大数据库额度。
        updated_at (datetime): 更新时间。
    """
    user_id: int
    max_databases: int
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# 4.1.4 用户详情 - Project DTO
class AdminUserProjectItem(BaseModel):
    """管理员视角的用户项目条目。"""

    project_id: int
    project_name: str
    db_type: Optional[str] = None
    project_status: str
    created_at: datetime
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# 4.1.4 用户详情 - Login History DTO
class AdminUserLoginHistoryItem(BaseModel):
    """管理员视角的用户登录历史条目。"""

    login_id: int
    login_time: datetime
    logout_time: Optional[datetime] = None
    ip_address: str
    user_agent: Optional[str] = None
    login_status: str
    failure_reason: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# 4.1.4 用户详情 - Response
class AdminUserDetailResponse(BaseModel):
    """管理员查看用户详情响应。"""

    user_id: int
    username: str
    email: str
    status: Literal["normal", "suspended", "banned"]
    max_databases: int
    project_count: int
    last_login_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    projects: List[AdminUserProjectItem] = Field(default_factory=list)
    login_history: List[AdminUserLoginHistoryItem] = Field(default_factory=list)


# ----------------------------------------------------------------------
# 4.2. 公告管理 Schemas
# ----------------------------------------------------------------------

class AnnouncementCreateRequest(BaseModel):
    """
    创建公告请求 Schema。

    Attributes:
        title (str): 公告标题。
        content (str): 公告内容。
        status (str): 公告状态 (默认 "published")。
    """
    title: str = Field(..., min_length=1, max_length=100)
    content: str
    status: Literal['draft', 'published'] = 'published'


class AnnouncementUpdateRequest(BaseModel):
    """
    更新公告请求 Schema。

    Attributes:
        title (Optional[str]): 公告标题。
        content (Optional[str]): 公告内容。
        status (Optional[str]): 公告状态。
    """
    title: Optional[str] = None
    content: Optional[str] = None
    status: Optional[Literal["draft", "published", "unpublished", "expired"]] = None


class AnnouncementResponse(BaseModel):
    """
    公告响应 Schema。

    Attributes:
        announcement_id (int): 公告 ID。
        title (str): 公告标题。
        content (str): 公告内容。
        status (str): 公告状态。
        created_at (datetime): 创建时间。
        updated_at (Optional[datetime]): 更新时间。
        created_by (Optional[int]): 创建人 ID。
    """
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
    """
    管理员列表单项 Schema。

    Attributes:
        user_id (int): 用户 ID。
        username (str): 用户名。
        email (str): 邮箱。
        last_login_at (Optional[datetime]): 最后登录时间。
        is_online (bool): 是否在线。
    """
    user_id: int
    username: str
    email: str
    last_login_at: Optional[datetime]
    is_online: bool = False

    model_config = ConfigDict(from_attributes=True)


# 管理员列表响应
class AdminListResponse(PaginatedResponseSchema):
    """
    管理员列表响应 Schema。

    Attributes:
        items (List[AdminListItem]): 管理员列表项。
    """
    items: List[AdminListItem]


# 违规记录单项
class ViolationLogListItem(BaseModel):
    """
    违规记录列表单项 Schema。

    Attributes:
        violation_id (int): 违规记录 ID。
        user_id (int): 用户 ID。
        username (str): 用户名。
        risk_level (str): 风险等级。
        resolution_status (str): 处理状态。
        created_at (datetime): 创建时间。
    """
    violation_id: int
    user_id: int
    username: str
    risk_level: str
    resolution_status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# 违规记录列表响应
class ViolationLogListResponse(PaginatedResponseSchema):
    """
    违规记录列表响应 Schema。

    Attributes:
        items (List[ViolationLogListItem]): 违规记录列表项。
    """
    items: List[ViolationLogListItem]


# 系统统计响应
class AdminStatsResponse(BaseModel):
    """
    系统统计响应 Schema。

    Attributes:
        active_users_today (int): 今日活跃用户数。
        total_projects (int): 项目总数。
        query_count_today (int): 今日查询数。
        high_risk_operations_today (int): 今日高风险操作数。
        system_health (str): 系统健康状况。
    """
    active_users_today: int
    total_projects: int
    query_count_today: int
    high_risk_operations_today: int
    system_health: Literal["good", "warning", "critical"]
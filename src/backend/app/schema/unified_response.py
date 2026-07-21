"""
统一响应 Schema。

本模块定义了 API 接口的标准响应格式，采用 "Always 200" 策略。
无论业务成功还是失败，HTTP 状态码始终返回 200 OK。
前端通过 Body 内的 code 字段来判断业务是否成功。
"""

# backend/app/schema/unified_response.py

from datetime import datetime
from pydantic import BaseModel, Field
from typing import Generic, TypeVar, Optional, Literal, Dict, Any

# 基础配置：泛型类型变量
# 通用数据类型变量（用于响应的数据字段）
T = TypeVar("T")

class UnifiedResponse(BaseModel, Generic[T]):
    """统一响应模型（Always 200 策略）
    
    Attributes:
        code: 业务状态码。0 代表成功，1xxxx 代表参数错误，2xxxx 代表业务逻辑阻断等。
        message: 展示给用户的提示信息。
        data: 业务数据。
    """
    code: int = Field(0, description="业务状态码。0 代表成功，1xxxx 代表参数错误，2xxxx 代表业务逻辑阻断等")
    message: str = Field("操作成功", description="展示给用户的提示信息")
    data: Optional[T] = Field(None, description="业务数据")

    @classmethod
    def success(
        cls,
        data: Optional[T] = None,
        message: str = "操作成功"
    ) -> "UnifiedResponse[T]":
        """快捷创建成功响应"""
        return cls(code=0, message=message, data=data)

    @classmethod
    def error(
        cls,
        code: int,
        message: str,
        data: Optional[T] = None
    ) -> "UnifiedResponse[T]":
        """快捷创建错误响应"""
        return cls(code=code, message=message, data=data)

# 分页响应数据模型（用于嵌套在 UnifiedResponse 的 data 字段中）
class PageData(BaseModel, Generic[T]):
    """分页数据模型
    
    Attributes:
        total: 符合条件的总记录数
        page: 当前页码（从 1 开始）
        page_size: 每页显示的记录数
        items: 当前页的记录列表
    """
    total: int = Field(..., description="符合条件的总记录数")
    page: int = Field(..., description="当前页码（从 1 开始）")
    page_size: int = Field(..., description="每页显示的记录数")
    items: Optional[T] = Field(None, description="当前页的记录列表")

    @classmethod
    def create(
        cls,
        total: int,
        page: int,
        page_size: int,
        items: Optional[T] = None
    ) -> "PageData[T]":
        """快捷创建分页数据"""
        return cls(total=total, page=page, page_size=page_size, items=items)

# 专用数据模型（各业务场景的具体数据结构）
class LoginData(BaseModel):
    """登录成功专用数据模型"""
    access_token: str = Field(..., description="JWT 访问令牌")
    token_type: str = Field("bearer", description="令牌类型（固定为 bearer）")
    user: Dict[str, Any] = Field(..., description="用户基础信息（建议后续替换为 UserInfo 模型，字段更明确）")

class LoginHistoryData(BaseModel):
    """登录历史分页记录数据模型"""
    login_id: int = Field(..., description="登录记录 ID")
    login_time: str = Field(..., description="登录时间（格式：YYYY-MM-DD HH:MM:SS）")
    logout_time: str = Field(..., description="登出时间（未登出则为 null 或 空字符串）")
    ip_address: str = Field(..., description="登录 IP 地址")
    device_info: str = Field(..., description="登录设备信息（如浏览器、手机型号）")
    login_status: str = Field(..., description="登录状态（如 success/failed/online）")

class ProjectListData(BaseModel):
    """项目列表分页记录数据模型"""
    project_id: int = Field(..., description="项目 ID")
    project_name: str = Field(..., description="项目名称")
    description: str = Field(..., description="项目描述")
    project_status: Literal['initializing', 'active', 'pending_confirmation', 'deleted', 'completed'] = Field(..., description="项目状态：初始化/激活/待确认/已删除/已完成")
    updated_at: datetime = Field(..., description="最后更新时间（UTC 时间或本地时间，建议统一格式）")

class SessionListData(BaseModel):
    """会话列表分页记录数据模型"""
    session_id: int = Field(..., description="会话 ID")
    session_name: str = Field(..., description="会话名称")
    last_activity: datetime = Field(..., description="最后活动时间（UTC 时间或本地时间，建议统一格式）")

# 简化类型别名（减少路由层泛型冗余写法）
LoginSuccessResponse = UnifiedResponse[LoginData]
LoginHistoryPageResponse = UnifiedResponse[PageData[list[LoginHistoryData]]]
ProjectListPageResponse = UnifiedResponse[PageData[list[ProjectListData]]]
SessionListPageResponse = UnifiedResponse[PageData[list[SessionListData]]]
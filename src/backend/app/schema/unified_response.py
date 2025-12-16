"""
统一响应 Schema。

本模块定义了 API 接口的标准响应格式，包括成功响应、分页响应和错误响应的泛型结构。
确保所有 API 返回一致的数据结构，便于前端解析。
"""

# backend/app/schema/unified_response.py

from datetime import datetime
from pydantic import BaseModel, Field
from typing import Generic, TypeVar, Optional, Literal, Dict, Any
from fastapi import status

# 基础配置：泛型类型变量
# 通用数据类型变量（用于成功响应、分页响应的数据字段）
T = TypeVar("T")

#一、错误响应相关模型（补充完整，覆盖业务冲突/字段错误）
class ErrorDetail(BaseModel):
    """错误详情模型"""
    field: Optional[str] = Field(None, description="出错字段（如 email、username、project_name）")
    issue: Optional[str] = Field(None, description="具体错误原因（如“邮箱已被注册”“项目状态非法”）")

class ErrorResponse(BaseModel):
    """统一错误响应模型（对应 4xx/5xx 状态码，如 409 冲突、401 未授权）"""
    error: Dict[str, Any] = Field(..., description="错误核心信息")

    @classmethod
    def create(
        cls,
        code: str | int,
        message: str,
        details: Optional[ErrorDetail | Dict[str, Any]] = None
    ) -> "ErrorResponse":
        """快捷创建错误响应（避免手动构造字典，格式更统一）"""
        error_data = {
            "code": str(code),  # 统一转为字符串，避免数字/字符串混用
            "message": message
        }
        if details:
            error_data["details"] = details.model_dump(exclude_none=True) if isinstance(details, ErrorDetail) else details
        return cls(error=error_data)

# 二、成功响应相关模型（覆盖普通成功、无内容成功）
class UnifiedSuccessResponse(BaseModel, Generic[T]):
    """统一成功响应模型（对应 200/201 等带数据的成功状态码）"""
    code: int = Field(status.HTTP_200_OK, description="HTTP 状态码（默认 200）")
    message: str = Field("操作成功", description="成功提示信息（可自定义）")
    data: Optional[T] = Field(None, description="业务数据（如登录信息、单条记录）")

    @classmethod
    def create(
        cls,
        data: Optional[T] = None,
        code: int = status.HTTP_200_OK,
        message: str = "操作成功"
    ) -> "UnifiedSuccessResponse[T]":
        """快捷创建成功响应（减少重复代码）"""
        return cls(code=code, message=message, data=data)

class NoContentResponse(BaseModel):
    """无内容成功响应（对应 204 No Content，如删除操作成功）"""
    pass

# 三、分页响应相关模型（统一分页格式）
class UnifiedPageResponse(BaseModel, Generic[T]):
    """统一分页响应模型（对应列表查询、分页查询场景）"""
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
    ) -> "UnifiedPageResponse[T]":
        """快捷创建分页响应（格式统一，无需手动赋值字段）"""
        return cls(total=total, page=page, page_size=page_size, items=items)

#  四、专用数据模型（各业务场景的具体数据结构）
class LoginData(BaseModel):
    """登录成功专用数据模型（用于 UnifiedSuccessResponse 的 data 字段）"""
    access_token: str = Field(..., description="JWT 访问令牌")
    token_type: str = Field("bearer", description="令牌类型（固定为 bearer）")
    user: Dict[str, Any] = Field(..., description="用户基础信息（建议后续替换为 UserInfo 模型，字段更明确）")

class LoginHistoryData(BaseModel):
    """登录历史分页记录数据模型（用于 UnifiedPageResponse 的 items 字段）"""
    login_id: int = Field(..., description="登录记录 ID")
    login_time: str = Field(..., description="登录时间（格式：YYYY-MM-DD HH:MM:SS）")
    logout_time: str = Field(..., description="登出时间（未登出则为 null 或 空字符串）")
    ip_address: str = Field(..., description="登录 IP 地址")
    device_info: str = Field(..., description="登录设备信息（如浏览器、手机型号）")
    login_status: str = Field(..., description="登录状态（如 success/failed/online）")

class ProjectListData(BaseModel):
    """项目列表分页记录数据模型（用于 UnifiedPageResponse 的 items 字段）"""
    project_id: int = Field(..., description="项目 ID")
    project_name: str = Field(..., description="项目名称")
    description: str = Field(..., description="项目描述")
    project_status: Literal['initializing', 'activate', 'deleted'] = Field(..., description="项目状态：初始化/激活/已删除")
    updated_at: datetime = Field(..., description="最后更新时间（UTC 时间或本地时间，建议统一格式）")

class SessionListData(BaseModel):
    """会话列表分页记录数据模型（用于 UnifiedPageResponse 的 items 字段）"""
    session_id: int = Field(..., description="会话 ID")
    session_name: str = Field(..., description="会话名称")
    last_activity: datetime = Field(..., description="最后活动时间（UTC 时间或本地时间，建议统一格式）")

# 五、简化类型别名（减少路由层泛型冗余写法）
# 登录成功响应（直接使用，无需重复写 UnifiedSuccessResponse[LoginData]）
LoginSuccessResponse = UnifiedSuccessResponse[LoginData]

# 登录历史分页响应（直接使用）
LoginHistoryPageResponse = UnifiedPageResponse[list[LoginHistoryData]]

# 项目列表分页响应（直接使用）
ProjectListPageResponse = UnifiedPageResponse[list[ProjectListData]]

# 会话列表分页响应（直接使用）
SessionListPageResponse = UnifiedPageResponse[list[SessionListData]]
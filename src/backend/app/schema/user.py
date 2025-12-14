"""
用户管理 Schema。

本模块定义了用户个人信息的查询、更新、修改密码及头像等操作的请求和响应模型。
"""

from pydantic import BaseModel, Field, EmailStr, field_validator, model_validator, ConfigDict
from typing import Optional, Literal, List, Any
from datetime import datetime


# 基础用户信息
class UserBase(BaseModel):
    """
    用户基础信息 Schema。

    Attributes:
        username (str): 用户名。
        email (EmailStr): 邮箱。
    """
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
# 当前用户响应
class UserMe(BaseModel):
    """
    当前登录用户详情 Schema。

    Attributes:
        user_id (int): 用户 ID。
        username (str): 用户名。
        email (EmailStr): 邮箱。
        status (str): 用户状态。
        used_databases (int): 已使用的数据库项目数。
        max_databases (int): 最大数据库额度。
        avatar_url (Optional[str]): 头像 URL。
        is_admin (bool): 是否管理员。
        last_login_at (Optional[datetime]): 最后登录时间。
        created_at (datetime): 注册时间。
    """
    user_id: int
    username: str
    email: EmailStr
    status: Literal['normal', 'suspended', 'banned']
    #  字段名必须与数据库一致 (used_databases)
    used_databases: int
    max_databases: int
    avatar_url: Optional[str] = None
    is_admin: bool
    # 字段名必须与数据库一致 (last_login_at)
    last_login_at: Optional[datetime] = None
    created_at: datetime
    # 必须包含此配置，且缩进要在 class 内部！
    model_config = ConfigDict(from_attributes=True)

# 更新用户名
class UserUpdateUsername(BaseModel):
    """
    更新用户名请求 Schema。

    Attributes:
        username (str): 新用户名。
    """
    username: str = Field(..., min_length=3, max_length=50)

# 更新用户邮箱请求
class UserUpdateEmailRequest(BaseModel):
    """
    更新邮箱请求 Schema。

    Attributes:
        new_email (EmailStr): 新邮箱地址。
    """
    new_email: EmailStr

# 更新用户邮箱确认
class UserUpdateEmailConfirm(BaseModel):
    """
    更新邮箱确认 Schema。

    Attributes:
        new_email (EmailStr): 新邮箱地址。
        code (str): 验证码。
    """
    new_email: EmailStr
    code: str = Field(..., min_length=6, max_length=6, description="验证码")

# 更新头像
class UserUpdateAvatar(BaseModel):
    """
    更新头像请求 Schema。

    Attributes:
        avatar_url (Optional[str]): 头像 URL。
    """
    avatar_url: Optional[str] = None

# 更新密码
class UserUpdatePassword(BaseModel):
    """
    更新密码请求 Schema。

    Attributes:
        old_password (str): 旧密码。
        new_password (str): 新密码。
        confirm_password (str): 确认密码。
    """
    old_password: str = Field(..., min_length=6, max_length=50, description="旧密码")
    new_password: str = Field(..., min_length=6, max_length=50, description="新密码")
    confirm_password: str = Field(..., min_length=6, max_length=50, description="确认密码")


    @model_validator(mode='before')
    @classmethod
    def passwords_match(cls, data: Any) -> Any:
        # Pydantic V2 的验证逻辑必须是 @model_validator 或 @field_validator
        if isinstance(data, dict):
            new_password = data.get('new_password')
            confirm_password = data.get('confirm_password')

            if new_password and confirm_password and new_password != confirm_password:
                raise ValueError('passwords do not match')
        return data


    model_config = ConfigDict(from_attributes=True)


# --- 1. 登录历史单项 DTO (用于 items 列表) ---
class LoginHistoryItem(BaseModel):
    """
    登录历史列表单项 Schema。

    Attributes:
        login_id (int): 登录记录 ID。
        login_time (datetime): 登录时间。
        logout_time (Optional[datetime]): 登出时间。
        ip_address (str): IP 地址。
        user_agent (Optional[str]): 设备信息。
        login_status (str): 登录状态。
    """
    login_id: int = Field(..., description="登录记录ID")
    login_time: datetime
    logout_time: Optional[datetime] = None
    ip_address: str
    # 假设设备信息映射到 user_agent
    user_agent: Optional[str] = Field(None, description="设备信息/User Agent")
    login_status: Literal['success', 'failed', 'expired', 'forced_logout']

    #实际 DB 中有 session_duration 和 failure_reason，可以按需添加

    model_config = ConfigDict(from_attributes=True)


# ----------------------------------------------------
# 2. 分页包装器 DTO (用于接口响应)
# ----------------------------------------------------
class PaginatedLoginHistory(BaseModel):
    """
    登录历史分页列表响应 DTO (Doc 3.1.7)
    """
    total: int = Field(..., description="总记录数")
    page: int = Field(1, description="当前页码")
    page_size: int = Field(10, description="每页记录数")  # Doc 要求默认 10

    # 列表项使用 LoginHistoryItem
    items: List['LoginHistoryItem']

    model_config = ConfigDict(from_attributes=True)
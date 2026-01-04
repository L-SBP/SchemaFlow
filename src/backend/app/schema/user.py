"""
用户管理 Schema。

本模块定义了用户个人信息的查询、更新、修改密码及头像等操作的请求和响应模型。
"""

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator, ConfigDict, validator
from typing import Optional, Literal, List, Any
from datetime import datetime
import re


# 基础用户信息
class UserBase(BaseModel):
    """
    用户基础信息 Schema。

    Attributes:
        username (str): 用户名。
        email (str): 邮箱。
    """
    username: str = Field(..., description="用户名")
    email: str
    
    @validator('username')
    def username_length(cls, v):
        if not 3 <= len(v) <= 50:
            raise ValueError('用户名长度必须在3到50个字符之间')
        return v
    
    @validator('email')
    def validate_email(cls, v):
        try:
            EmailStr.validate(v)
        except Exception:
            raise ValueError('邮箱格式不正确，请输入有效的邮箱地址')
        return v

# 当前用户响应
class UserMe(BaseModel):
    """
    当前登录用户详情 Schema。

    Attributes:
        user_id (int): 用户 ID。
        username (str): 用户名。
        email (str): 邮箱。
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
    email: str
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
    username: str = Field(..., description="用户名")
    
    @validator('username')
    def username_length(cls, v):
        if not 3 <= len(v) <= 50:
            raise ValueError('用户名长度必须在3到50个字符之间')
        return v

# 更新用户邮箱请求
class UserUpdateEmailRequest(BaseModel):
    """
    更新邮箱请求 Schema。

    Attributes:
        new_email (str): 新邮箱地址。
    """
    new_email: str  # 修改为 str 类型
    
    @validator('new_email')
    def validate_new_email(cls, v):
        try:
            EmailStr.validate(v)
        except Exception:
            raise ValueError('邮箱格式不正确，请输入有效的邮箱地址')
        return v

# 更新用户邮箱确认
class UserUpdateEmailConfirm(BaseModel):
    """
    更新邮箱确认 Schema。

    Attributes:
        new_email (str): 新邮箱地址。
        code (str): 验证码。
    """
    new_email: str
    code: str = Field(..., description="验证码")
    
    @validator('code')
    def code_length(cls, v):
        if not 6 <= len(v) <= 6:
            raise ValueError('验证码必须为6个字符')
        return v
    
    @validator('new_email')
    def validate_new_email(cls, v):
        try:
            EmailStr.validate(v)
        except Exception:
            raise ValueError('邮箱格式不正确，请输入有效的邮箱地址')
        return v

# 更新头像
class UserUpdateAvatar(BaseModel):
    """
    更新头像请求 Schema。

    Attributes:
        avatar_url (Optional[str]): 头像 URL。
    """
    avatar_url: Optional[str] = None

    @field_validator('avatar_url')
    @classmethod
    def validate_avatar_url(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v

        value = v.strip()
        if value == '':
            return None

        # 1) Base64 Data URL：data:image/png;base64,...
        if value.lower().startswith('data:'):
            match = re.match(r'^data:(?P<mime>[^;]+);base64,', value, flags=re.IGNORECASE)
            if not match:
                raise ValueError('头像数据格式不正确')
            mime = match.group('mime').lower()
            if mime not in {'image/png', 'image/jpeg', 'image/gif'}:
                raise ValueError('头像只支持 PNG、JPG、GIF 格式')
            return value

        # 2) 普通 URL：按后缀名限制（防止明显的非图片地址）
        lower = value.lower()
        if not re.search(r'\.(png|jpe?g|gif)(\?.*)?$', lower):
            raise ValueError('头像只支持 PNG、JPG、GIF 格式')
        return value

# 更新密码
class UserUpdatePassword(BaseModel):
    """
    更新密码请求 Schema。

    Attributes:
        old_password (str): 旧密码。
        new_password (str): 新密码。
        confirm_password (str): 确认密码。
    """
    old_password: str = Field(..., description="旧密码")
    new_password: str = Field(..., description="新密码")
    confirm_password: str = Field(..., description="确认密码")
    
    @model_validator(mode='after')
    def check_password_length(self) -> 'UserUpdatePassword':
        for pwd in [self.old_password, self.new_password, self.confirm_password]:
            if not 6 <= len(pwd) <= 50:
                raise ValueError('密码长度必须在6到50个字符之间')
        return self
    
    @model_validator(mode='before')
    @classmethod
    def passwords_match(cls, data: Any) -> Any:
        # Pydantic V2 的验证逻辑必须是 @model_validator 或 @field_validator
        if isinstance(data, dict):
            new_password = data.get('new_password')
            confirm_password = data.get('confirm_password')

            if new_password and confirm_password and new_password != confirm_password:
                raise ValueError('两次输入的密码不一致')
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
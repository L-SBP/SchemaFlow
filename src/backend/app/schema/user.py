from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, Literal
from datetime import datetime

from pydantic.v1 import HttpUrl

# 基础用户信息
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, discriminator="用户名")
    email: EmailStr

# 当前用户响应
class UserMe(BaseModel):
    user_id: int
    username: str
    email: EmailStr
    status: Literal['normal', 'suspended', 'banned']
    user_databases: int
    max_databases: int
    avatar_url: Optional[HttpUrl] = None
    is_admin: bool
    last_login_in: Optional[datetime] = None
    created_at: datetime

# 更新用户名
class UserUpdateUsername(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, discriminator="用户名")

# 更新用户邮箱请求
class UserUpdateEmailRequest(BaseModel):
    new_email: EmailStr

# 更新用户邮箱确认
class UserUpdateEmailConfirm(BaseModel):
    new_email: EmailStr
    code: str = Field(..., min_length=6, max_length=6, description="验证码")

# 更新头像
class UserUpdateAvatar(BaseModel):
    avatar_url: Optional[HttpUrl] = None

# 更新密码
class UserUpdatePassword(BaseModel):
    old_password: str = Field(..., min_length=6, max_length=50, description="旧密码")
    new_password: str = Field(..., min_length=6, max_length=50, description="新密码")
    confirm_password: str = Field(..., min_length=6, max_length=50, description="确认密码")

    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('passwords do not match')
        return v


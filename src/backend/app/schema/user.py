from pydantic import BaseModel, Field, EmailStr, field_validator, model_validator, ConfigDict
from typing import Optional, Literal, List, Any
from datetime import datetime

from pydantic import HttpUrl

# 基础用户信息
class UserBase(BaseModel):
    # 移除错误的 discriminator 属性
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
# 当前用户响应
class UserMe(BaseModel):
    user_id: int
    username: str
    email: EmailStr
    status: Literal['normal', 'suspended', 'banned']
    # 修正点1: 字段名必须与数据库一致 (used_databases)
    used_databases: int
    max_databases: int
    avatar_url: Optional[HttpUrl] = None
    is_admin: bool
    # 修正点2: 字段名必须与数据库一致 (last_login_at)
    last_login_at: Optional[datetime] = None
    created_at: datetime
    # 修正点3: 必须包含此配置，且缩进要在 class 内部！
    model_config = ConfigDict(from_attributes=True)

# 更新用户名
class UserUpdateUsername(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)

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

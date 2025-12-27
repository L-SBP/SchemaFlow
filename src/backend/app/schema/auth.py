"""
认证授权 Schema。

本模块定义了用户注册、登录、密码重置及验证码发送相关的请求和响应模型。
"""

from pydoc import describe
from pydantic import BaseModel, validator, Field


# 发送验证码
class UserSendCode(BaseModel):
    """
    发送验证码请求 Schema。

    Attributes:
        email (str): 接收验证码的邮箱。
    """
    email: str = Field(..., description="邮箱")
    
    @validator('email')
    def email_length(cls, v):
        if not 3 <= len(v) <= 50:
            raise ValueError('邮箱长度必须在3到50个字符之间')
        return v

# 用户注册
class UserRegister(BaseModel):
    """
    用户注册请求 Schema。

    Attributes:
        username (str): 用户名。
        email (str): 邮箱。
        password (str): 密码。
        confirm_password (str): 确认密码。
        verification_code (str): 验证码。
    """
    username: str = Field(..., description="用户名")
    email: str = Field(..., description="邮箱")
    password: str = Field(..., description="密码")
    confirm_password: str = Field(..., description="确认密码")
    verification_code: str = Field(..., description="验证码")

    @validator('username')
    def username_length(cls, v):
        if not 3 <= len(v) <= 50:
            raise ValueError('用户名长度必须在3到50个字符之间')
        return v

    @validator('email')
    def email_length(cls, v):
        if not 3 <= len(v) <= 50:
            raise ValueError('邮箱长度必须在3到50个字符之间')
        return v

    @validator('password')
    def password_length(cls, v):
        if not 6 <= len(v) <= 50:
            raise ValueError('密码长度必须在6到50个字符之间')
        return v

    @validator('confirm_password')
    def password_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('两次输入的密码不一致')
        return v

# 用户登录
class UserLogin(BaseModel):
    """
    用户登录请求 Schema。

    Attributes:
        username (str): 用户名。
        password (str): 密码。
    """
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")

    @validator('username')
    def username_length(cls, v):
        if not 3 <= len(v) <= 50:
            raise ValueError('用户名长度必须在3到50个字符之间')
        return v

    @validator('password')
    def password_length(cls, v):
        if not 6 <= len(v) <= 50:
            raise ValueError('密码长度必须在6到50个字符之间')
        return v


class ForgotPasswordRequest(BaseModel):
    """忘记密码：请求发送重置验证码邮件。"""

    email: str = Field(..., description="邮箱")

    @validator('email')
    def email_length(cls, v):
        if not 3 <= len(v) <= 50:
            raise ValueError('邮箱长度必须在3到50个字符之间')
        return v


class ResetPasswordRequest(BaseModel):
    """重置密码：输入邮箱验证码后直接重置。"""

    email: str = Field(..., description="邮箱")
    verification_code: str = Field(..., description="验证码")
    new_password: str = Field(..., description="新密码")
    confirm_password: str = Field(..., description="确认新密码")

    @validator('email')
    def email_length(cls, v):
        if not 3 <= len(v) <= 50:
            raise ValueError('邮箱长度必须在3到50个字符之间')
        return v

    @validator('verification_code')
    def verification_code_length(cls, v):
        if len(v) != 6:
            raise ValueError('验证码必须是6个字符')
        return v

    @validator('new_password')
    def new_password_length(cls, v):
        if not 6 <= len(v) <= 50:
            raise ValueError('密码长度必须在6到50个字符之间')
        return v

    @validator('confirm_password')
    def password_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('两次输入的密码不一致')
        return v
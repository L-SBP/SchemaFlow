"""
认证授权 Schema。

本模块定义了用户注册、登录、密码重置及验证码发送相关的请求和响应模型。
"""

from pydantic import BaseModel, Field, validator


# 发送验证码
class UserSendCode(BaseModel):
    """
    发送验证码请求 Schema。

    Attributes:
        email (str): 接收验证码的邮箱。
    """
    email: str = Field(..., min_length=3, max_length=50)

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
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=50)
    confirm_password: str = Field(..., min_length=6, max_length=50)
    verification_code:  str = Field(..., min_length=6, max_length=6)

    @validator('confirm_password')
    def password_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('Password do not match')
        return v

# 用户登录
class UserLogin(BaseModel):
    """
    用户登录请求 Schema。

    Attributes:
        username (str): 用户名。
        password (str): 密码。
    """
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=50)
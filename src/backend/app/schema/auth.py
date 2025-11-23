from pydantic import BaseModel, Field, validator

# 发送验证码
class UserSendCode(BaseModel):
    email: str = Field(..., min_length=3, max_length=50, discriminator="注册邮箱地址")

# 用户注册
class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, discriminator="用户名")
    email: str = Field(..., min_length=3, max_length=50, discriminator="邮箱")
    password: str = Field(..., min_length=6, max_length=50, discriminator="密码")
    confirm_password: str = Field(..., min_length=6, max_length=50, discriminator="确认密码")
    code:  str = Field(..., min_length=6, max_length=6, discriminator="验证码")

    @validator('confirm_password')
    def password_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('Password do not match')
        return v

# 用户登录
class UserLogin(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, discriminator="用户名或邮箱")
    password: str = Field(..., min_length=6, max_length=50, discriminator="密码")

# 自动登录
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

# 登录响应
class TokenPayload(BaseModel):
    sub: str = Field(..., discriminator="用户ID")
    exp: int
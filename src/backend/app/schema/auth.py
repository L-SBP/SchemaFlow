from pydantic import BaseModel, Field, validator


# 发送验证码
class UserSendCode(BaseModel):
    email: str = Field(..., min_length=3, max_length=50)

# 用户注册
class UserRegister(BaseModel):
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
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=50)
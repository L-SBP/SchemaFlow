from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone

from server import config
from core.exceptions import TokenInvalidException

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# 密码验证
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# 密码加密
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


# 解析 JWT Token 后的数据载体
class TokenData(BaseModel):
    username: str | None = None

# 解析 JWT Token
def decode_jwt_token(token: str) -> TokenData:
    """
    解析 JWT Token，返回 TokenData
    失败则抛业务异常
    """
    try:
        payload = jwt.decode(
            token,
            config.jwt.secret_key,
            algorithms=[config.jwt.algorithm]
        )
        username: str = payload.get("sub")
        if username is None:
            raise TokenInvalidException()
        return TokenData(username=username)
    except JWTError:
        raise TokenInvalidException()

# 创建 JWT Token
def create_access_token(data: dict) -> str:
    """
    创建 JWT Token

    :return jwt字符串
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=config.jwt.expire_time)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, config.jwt.secret_key, algorithm=config.jwt.algorithm)
    return encoded_jwt
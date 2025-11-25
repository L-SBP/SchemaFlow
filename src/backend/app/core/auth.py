from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone

from server import config
from core.exceptions import TokenInvalidException
from core.log import log

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# 密码验证
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# 密码加密
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# 解析 JWT Token
def decode_jwt_token(token: str) -> int:
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
        log.info(f"Decoded JWT Token: {payload}")
        user_id: str = payload.get("sub")
        log.info(f"User ID: {user_id}")

        if user_id is None:
            log.error("JWT payload has no 'sub' field")
            raise TokenInvalidException()
        exp_timestamp = payload.get("exp")
        if exp_timestamp:
            from datetime import datetime
            exp_time = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
            current_time = datetime.now(tz=timezone.utc)
            if current_time > exp_time:
                log.error(f"JWT Token expired: exp={exp_time}, current={current_time}")

        return int(user_id)
    except JWTError as e:
        log.error(f"JWT decode failed with error: {str(e)}")
        raise TokenInvalidException()

# 创建 JWT Token
def create_access_token(data: dict) -> str:
    """
    创建 JWT Token

    :return jwt字符串
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(seconds=config.jwt.token_expire_time_seconds)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, config.jwt.secret_key, algorithm=config.jwt.algorithm)
    return encoded_jwt
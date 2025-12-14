# src/backend/app/core/auth.py

from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import jwt, JWTError
from passlib.context import CryptContext
from core.config import settings # 使用 settings
from core.exceptions import TokenInvalidException
from core.log import log

# 密码哈希上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 1. 密码验证
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# 2. 密码加密
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# 3. 解析 JWT Token (纯函数，不查 Redis，只解密)
def decode_jwt_token(token: str) -> int:
    try:
        payload = jwt.decode(
            token,
            settings.jwt.secret_key,
            algorithms=[settings.jwt.algorithm]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise TokenInvalidException()
            
        return int(user_id)
    except JWTError:
        raise TokenInvalidException()

# 4. 创建 JWT Token
def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(seconds=settings.jwt.token_expire_time_seconds)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.jwt.secret_key, algorithm=settings.jwt.algorithm)
    return encoded_jwt
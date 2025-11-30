from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
from pydantic import BaseModel

# 使用 core.config，这通常是标准的路径
from core.config import config
from core.exceptions import TokenInvalidException
from core.log import log
# 导入 Redis 获取函数
from redis.redis import get_redis

# 密码哈希上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 方案定义
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# 1. 密码验证
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# 2. 密码加密
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


# 3. 解析 JWT Token
def decode_jwt_token(token: str) -> int:
    """
    解析 JWT Token，返回 user_id (int)
    失败则抛出 TokenInvalidException 业务异常
    """
    try:
        payload = jwt.decode(
            token,
            config.jwt.secret_key,
            algorithms=[config.jwt.algorithm]
        )
        # log.info(f"Decoded JWT Token: {payload}") # 调试时可开启，生产环境建议关闭以防日志过大

        user_id: str = payload.get("sub")
        if user_id is None:
            log.error("JWT payload has no 'sub' field")
            raise TokenInvalidException()

        # 检查过期时间
        exp_timestamp = payload.get("exp")
        if exp_timestamp:
            exp_time = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
            current_time = datetime.now(tz=timezone.utc)
            if current_time > exp_time:
                log.error(f"JWT Token expired: exp={exp_time}, current={current_time}")
                raise TokenInvalidException()

        log.info(f"User ID from token: {user_id}")
        return int(user_id)

    except JWTError as e:
        log.error(f"JWT decode failed with error: {str(e)}")
        raise TokenInvalidException()


# 4. 创建 JWT Token
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


# 5. 获取当前活跃用户 ID (依赖注入用)
async def get_current_active_user(
        token: str = Depends(oauth2_scheme)
) -> int:
    """
    负责解析 Token，检查是否过期/无效，返回 user_id。
    注意：此函数不查数据库，只解密 Token。查库逻辑请在 deps.py 中基于此 user_id 进行。
    """
    # 检查 Token 是否在 Redis 白名单中
    redis = get_redis()
    if redis:
        # 这里的 key 格式必须与 user_service.service_save_token_in_redis 保持一致
        token_key = f"token:{token}"
        is_valid = await redis.get(token_key)

        if not is_valid:
            log.warning(f"Token invalid (logged out or expired in redis): {token[:10]}...")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked (logged out)",
                headers={"WWW-Authenticate": "Bearer"},
            )

    try:
        user_id = decode_jwt_token(token)
        return user_id
    except TokenInvalidException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
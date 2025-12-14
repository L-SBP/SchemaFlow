"""
认证核心工具模块。
提供密码哈希验证、加密，以及 JWT Token 的生成和解析功能。
"""

# backend/app/core/auth.py

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
    """
    验证密码是否匹配。

    Args:
        plain_password (str): 明文密码。
        hashed_password (str): 哈希后的密码。

    Returns:
        bool: 如果密码匹配返回 True，否则返回 False。
    """
    return pwd_context.verify(plain_password, hashed_password)

# 2. 密码加密
def get_password_hash(password: str) -> str:
    """
    对密码进行哈希加密。

    Args:
        password (str): 明文密码。

    Returns:
        str: 加密后的哈希字符串。
    """
    return pwd_context.hash(password)

# 3. 解析 JWT Token (纯函数，不查 Redis，只解密)
def decode_jwt_token(token: str) -> int:
    """
    解析 JWT Token 获取用户 ID。

    Args:
        token (str): JWT Token 字符串。

    Returns:
        int: 用户 ID。

    Raises:
        TokenInvalidException: 如果 Token 无效或过期。
    """
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
    """
    创建 JWT 访问令牌。

    Args:
        data (dict): 需要编码到 Token 中的数据（如 sub）。

    Returns:
        str: 生成的 JWT Token 字符串。
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(seconds=settings.jwt.token_expire_time_seconds)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.jwt.secret_key, algorithm=settings.jwt.algorithm)
    return encoded_jwt

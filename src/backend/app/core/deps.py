"""
依赖注入模块。

提供数据库引擎、会话、认证等的依赖注入功能。
"""

# backend/app/core/deps.py

from typing import AsyncGenerator
from fastapi import Request, Depends, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from sqlalchemy import select

from core.database import PsqlHelper, SQLAlchemyError
from core.exceptions import DatabaseOperationFailedException, ForbiddenException, ItemNotFoundException
from core.config import settings
from core.auth import decode_jwt_token
from models.user_account import UserAccount
from core.log import log

# --- 定义 OAuth2 流程 (Swagger 用的那个) ---

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.app.api}/auth/swagger_login" 
)

# 1. DB 引擎
async def get_engine(request: Request) -> AsyncEngine:
    """
    从 Request 对象中获取数据库异步引擎。

    Args:
        request (Request): FastAPI 请求对象。

    Returns:
        AsyncEngine: 数据库异步引擎。
    """
    return request.app.state.psql_engine

# 2. DB 会话
async def get_db(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """
    获取数据库会话生成器。

    用于依赖注入，提供每个请求独立的数据库会话。

    Args:
        request (Request): FastAPI 请求对象。

    Yields:
        AsyncSession: 数据库异步会话。

    Raises:
        DatabaseOperationFailedException: 获取会话失败时抛出。
    """
    try:
        engine = await get_engine(request)
        async with PsqlHelper.get_session(engine) as session:
            yield session
    except SQLAlchemyError as e:
        raise DatabaseOperationFailedException("get database session") from e
    except AttributeError:
        raise DatabaseOperationFailedException("database engine not initialized")


# 3. 获取当前用户（带黑名单检查）
async def get_current_user(
    request: Request,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> UserAccount:
    """
    从 JWT Token 中获取当前用户。

    验证流程：
    1. 解析 JWT Token 获取用户 ID
    2. 查询数据库获取用户对象
    3. 检查用户账户状态（status: normal/suspended/banned）
    4. 检查请求频率是否超限（Redis）

    Args:
        request (Request): FastAPI 请求对象。
        token (str): JWT Token。
        db (AsyncSession): 数据库会话。

    Returns:
        UserAccount: 当前用户对象。

    Raises:
        ForbiddenException: Token 无效或用户被封禁时抛出。
        ItemNotFoundException: 用户不存在时抛出。
    """
    try:
        # 1. 解析 Token
        user_id = decode_jwt_token(token)
    except Exception as e:
        log.warning("Token 解析失败: {}", e)
        raise ForbiddenException(message="无效的认证凭据")

    try:
        # 2. 查询用户
        result = await db.execute(
            select(UserAccount).where(UserAccount.user_id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            log.warning("用户 {} 不存在", user_id)
            raise ItemNotFoundException(message="User not found")

        # 3. 检查用户状态
        if user.status == 'banned':
            log.warning("用户 {} 已被封禁", user_id)
            raise ForbiddenException(message="Account is banned. Please contact administrator.")
        
        if user.status == 'suspended':
            log.warning("用户 {} 账户异常，已被系统标记", user_id)
            raise ForbiddenException(message="Account is suspended due to abnormal activity. Please contact administrator.")

        # 4. 检查请求频率（可选的额外防护）
        from core.security import freq_limiter
        is_exceeded, count = freq_limiter.check_frequency(
            user_id,
            time_window=10,
            threshold=20
        )

        if is_exceeded:
            log.warning("用户 {} 请求频率超限: {} 请求/10秒", user_id, count)
            # 记录违规行为（log_violation 内部会自动检查是否需要标记为异常）
            try:
                from core.security import ViolationLogger
                ip_address = request.client.host if request.client else "127.0.0.1"
                await ViolationLogger.log_violation(
                    db,
                    user_id,
                    ViolationLogger.EVENT_EXCESSIVE_API_USAGE,
                    f"请求频率超限: {count} 请求在 10 秒内",
                    risk_level=ViolationLogger.RISK_MEDIUM,
                    ip_address=ip_address,
                    client_user_agent=request.headers.get("user-agent")
                )
                await db.commit()
            except ForbiddenException:
                raise
            except Exception as e:
                log.error("记录违规日志失败: {}", e)
                # 即使记录失败，仍然限制请求
                raise ForbiddenException(message="Too many requests")

        return user

    except Exception as e:
        log.error("获取当前用户失败: {}", e)
        raise ForbiddenException(message="Could not validate credentials")


# 4. 获取当前管理员用户（需要 admin 权限）
async def get_current_admin(
    current_user: UserAccount = Depends(get_current_user)
) -> UserAccount:
    """
    获取当前用户，并验证其是否为管理员。

    Args:
        current_user (UserAccount): 当前用户。

    Returns:
        UserAccount: 当前用户（已验证为管理员）。

    Raises:
        ForbiddenException: 用户不是管理员时抛出。
    """
    if not current_user.is_admin:
        log.warning("非管理员用户 {} 尝试访问管理员功能", current_user.user_id)
        raise ForbiddenException(message="Admin privileges required")

    return current_user

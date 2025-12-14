"""
依赖注入模块。

提供数据库引擎和会话的依赖注入功能。
"""

# backend/app/core/deps.py

from typing import AsyncGenerator
from fastapi import Request, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from core.database import PsqlHelper, SQLAlchemyError
from core.exceptions import DatabaseOperationFailedException
from core.config import settings

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

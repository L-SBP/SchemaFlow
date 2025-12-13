# src/backend/app/core/deps.py (完整整合版)

from typing import AsyncGenerator
from fastapi import Request, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from core.database import PsqlHelper, SQLAlchemyError
from core.exceptions import DatabaseOperationFailedException
from core.config import settings

# --- 定义 OAuth2 流程 (Swagger 用的那个) ---
# 这就是你之前报错找不到的 oauth2_scheme，我们在这里统一定义
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.app.api}/auth/swagger_login" 
)

# 1. DB 引擎
async def get_engine(request: Request) -> AsyncEngine:
    return request.app.state.psql_engine

# 2. DB 会话
async def get_db(request: Request) -> AsyncGenerator[AsyncSession, None]:
    try:
        engine = await get_engine(request)
        async with PsqlHelper.get_session(engine) as session:
            yield session
    except SQLAlchemyError as e:
        raise DatabaseOperationFailedException("get database session") from e
    except AttributeError:
        raise DatabaseOperationFailedException("database engine not initialized")
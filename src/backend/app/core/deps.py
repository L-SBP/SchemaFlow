# backend/app/core/deps.py (完整修正版本)

from typing import AsyncGenerator
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession


from core.database import PsqlHelper, SQLAlchemyError
from core.exceptions import DatabaseOperationFailedException  # 导入业务异常


async def get_engine(request: Request) -> AsyncEngine:
    """
    从 FastAPI app state 中获取已初始化的引擎
    """
    # 假设你的引擎被挂载在 app.state.psql_engine 上
    return request.app.state.psql_engine


async def get_db(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """
    核心数据库会话依赖：
    获取 AsyncSession，并在请求结束后自动关闭/回滚。
    """
    try:
        # 1. 获取引擎
        engine = await get_engine(request)

        # 2. 从引擎获取会话
        async with PsqlHelper.get_session(engine) as session:
            # 3. 产生会话供路由使用
            yield session

    except SQLAlchemyError as e:
        # 抛出业务异常，Service/Router 可以捕获
        raise DatabaseOperationFailedException("get database session") from e
    except AttributeError:
        # 捕获 app.state.psql_engine 未初始化错误 (启动时常见)
        raise DatabaseOperationFailedException("database engine not initialized")
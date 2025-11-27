# api/v1/deps.py
from typing import AsyncGenerator
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import get_engine
from core.database import PsqlHelper
from redis.redis import get_redis


async def get_db(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """
    真正的数据库会话依赖
    """
    engine = await get_engine(request)  # 获取真实引擎
    async with PsqlHelper.get_session(engine) as session:
        yield session

async def get_rd():
    """
    获取redis
    """
    return get_redis()
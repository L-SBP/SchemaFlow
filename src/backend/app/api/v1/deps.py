# api/v1/deps.py
from typing import AsyncGenerator
from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from core.deps import get_engine
from core.database import PsqlHelper
from core.log import log

async def get_db(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """
    真正的数据库会话依赖
    """
    log.info("get db 1")
    engine = await get_engine(request)  # 获取真实引擎
    log.info("get db 2")
    async with PsqlHelper.get_session(engine) as session:
        log.info("get db 3")
        yield session
        log.info("get db 4")
from fastapi import Request
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
)

async def get_engine(request: Request) -> AsyncEngine:
    """
    从 FastAPI app state 中获取已初始化的引擎
    """
    return request.app.state.psql_engine
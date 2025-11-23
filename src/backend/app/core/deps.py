from fastapi import Request
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
)

def get_engine_from_fastapi(request: Request) -> AsyncEngine:
    """
    从FastAPI请求中获取数据库引擎

    :param request: FastAPI请求对象
    :return: 数据库异步引擎对象
    """
    return request.app.state.psql_engine
"""Graph 节点使用的数据库会话工具 —— 懒加载避免循环导入"""

from core.database import PsqlHelper
from sqlalchemy.ext.asyncio import AsyncEngine


def _get_shared_engine() -> AsyncEngine:
    """获取 FastAPI 进程共享的 engine（运行时懒加载，避免模块级 import 循环）"""
    from server import my_app
    engine = my_app.state.psql_engine
    if engine is None:
        raise RuntimeError("psql_engine 尚未初始化")
    return engine


def _get_session():
    """便捷方法：直接从共享 engine 获取一个 session"""
    return PsqlHelper.get_session(_get_shared_engine())

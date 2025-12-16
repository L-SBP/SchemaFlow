"""
数据库连接核心模块。

提供 PostgreSQL 数据库的异步连接、会话管理及资源释放功能。
"""

# backend/app/core/database.py

from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncAttrs, AsyncSession, async_sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from collections.abc import AsyncGenerator
from fastapi import Depends

from config.base import DatabaseConfig

from sqlalchemy.exc import SQLAlchemyError



class Base(AsyncAttrs, DeclarativeBase):
    """
    数据库基础模型。

    所有 ORM 模型应继承此类。
    """

class PsqlHelper:
    """
    PostgresSQL 数据库连接处理类。
    """

    @staticmethod
    def _get_async_engine(db_config: DatabaseConfig) -> AsyncEngine:
        """
        创建异步引擎。

        Args:
            db_config (DatabaseConfig): 数据库配置对象。

        Returns:
            AsyncEngine: 初始化的数据库异步引擎。
        """

        return create_async_engine(
            url=db_config.sqlalchemy_database_url,
            echo=db_config.echo,
            pool_recycle=db_config.pool_recycle,
            pool_timeout=db_config.pool_timeout,
            pool_size=db_config.pool_size,
            max_overflow=db_config.max_overflow,
        )

    @staticmethod
    def _get_async_session(async_engine: AsyncEngine) -> AsyncSession:
        """
        获取异步会话生成器。

        Args:
            async_engine (AsyncEngine): 数据库异步引擎。

        Returns:
            AsyncSession: 异步会话实例。

        Raises:
            ValueError: 如果异步引擎未初始化。
        """

        if not async_engine:
            raise ValueError("Async engine is not initialized")
        return async_sessionmaker(
            bind=async_engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )()

    @classmethod
    async def init_conn_psql(cls, db_config: DatabaseConfig) -> AsyncEngine:
        """
        初始化数据库连接。

        创建引擎并确保所有模型表结构已创建。

        Args:
            db_config (DatabaseConfig): 数据库配置对象。

        Returns:
            AsyncEngine: 初始化的数据库异步引擎。
        """

        engine = cls._get_async_engine(db_config)
        # 创建Model对应的数据库库表
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        return engine

    @classmethod
    @asynccontextmanager
    async def get_session(cls, async_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
        """
        获取数据库会话 (使用上下文管理器)。

        提供事务管理的会话，自动提交或回滚。

        Args:
            async_engine (AsyncEngine): 已初始化的异步引擎。

        Yields:
            AsyncSession: 数据库会话。

        Raises:
            ValueError: 如果异步引擎未初始化。
            Exception: 数据库操作异常时抛出。
        """
        if not async_engine:
            raise ValueError("Async engine is not initialized")

        session_factory = async_sessionmaker(
            bind=async_engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
            class_=AsyncSession,
        )
        session = session_factory()

        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    @classmethod
    async def close_conn_psql(cls, async_engine: AsyncEngine) -> None:
        """
        关闭数据库连接。

        Args:
            async_engine (AsyncEngine): 数据库异步引擎。
        """

        await async_engine.dispose()

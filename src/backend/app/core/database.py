from sqlalchemy.ext.asyncio import AsyncEngine, AsyncAttrs, AsyncSession, async_sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from collections.abc import AsyncGenerator
from fastapi import Depends

from app.config.base import DatabaseConfig
from app.core.deps import get_engin_from_fastapi

class Base(AsyncAttrs, DeclarativeBase):
    """
    数据库基础模型
    """

class PsqlHelper:
    """
    PostgresSQL数据库连接处理类
    """

    @staticmethod
    def _get_async_engine(db_config: DatabaseConfig) -> AsyncEngine:
        """
        创建异步引擎

        :param db_config: 数据库配置
        :return: 数据库异步引擎
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
        获取异步会话生成器

        :param async_engine: 数据库异步引擎
        :return: 异步会话
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
        初始化数据库连接

        :param db_config: 数据库配置
        :return: 数据库异步引擎
        """

        engine = cls._get_async_engine(db_config)
        # 创建Model对应的数据库库表
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        return engine

    @classmethod
    async def get_session(cls, async_engine: AsyncEngine = Depends(get_engin_from_fastapi)) -> AsyncGenerator[AsyncSession, None]:
        """
        获取数据库会话

        :param async_engine: 数据库异步引擎
        :return: 数据库会话
        """

        async with cls._get_async_session(async_engine) as session:
            try:
                yield session
            finally:
                await session.close()

    @classmethod
    async def close_conn_psql(cls, async_engine: AsyncEngine) -> None:
        """
        关闭数据库连接

        :param async_engine: 数据库异步引擎
        """

        await async_engine.dispose()
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.config.base import MySQLConfig
from app.core.exceptions import InvalidOperationException
from app.core.log import log
from app.models import DatabaseInstance


class MysqlHelper:
    """
    MySQL数据库连接处理类(原生SQL执行模式)
    设计原则:
    1.超级用户(root) 连接仅用于初始化(创建用户和DB)
    2.业务SQL必须通过普通用户连接执行
    3.严格隔离权限，防止SQL注入
    """

    _root_engine: Optional[AsyncEngine] = None
    _user_engine: dict[int, AsyncEngine] = {}

    @classmethod
    async def init_root_engine(cls, mysql_config: MySQLConfig) -> None:
        """
        初始化root用户引擎
        :param mysql_config: yaml中mysql有关的配置
        :return:
        """
        connect_args = {
            "auth_plugin": mysql_config.plugin,
            "ssl": mysql_config.ssl
        }

        cls._root_engine = create_async_engine(
            mysql_config.sqlalchemy_database_url,
            connect_args=connect_args,
            pool_size=mysql_config.pool_size,
            pool_recycle=mysql_config.pool_recycle,
            pool_timeout=mysql_config.pool_timeout,
            max_overflow=mysql_config.max_overflow
        )

    @classmethod
    async def init_user_engine(cls, mysql_config: MySQLConfig, database_instance: DatabaseInstance):
        """
        初始化用户引擎
        :param mysql_config:
        :param database_instance:
        :return:
        """
        connect_args = {
            "auth_plugin": mysql_config.plugin,
            "ssl": mysql_config.ssl
        }

        cls._user_engine[database_instance.instance_id] = create_async_engine(
            database_instance.user_database_url,
            connect_args=connect_args,
            pool_size=mysql_config.pool_size,
            pool_recycle=mysql_config.pool_recycle,
            pool_timeout=mysql_config.pool_timeout,
            max_overflow=mysql_config.max_overflow
        )

    @classmethod
    async def close_root_engine(cls):
        """
        关闭root引擎
        :return:
        """
        await cls._root_engine.dispose()
        cls._root_engine = None
        log.info("close root engine")

    @classmethod
    async def close_user_engine(cls, database_instance: DatabaseInstance):
        """
        关闭用户引擎
        :param database_instance:
        :return:
        """
        await cls._user_engine[database_instance.instance_id].dispose()
        del cls._user_engine[database_instance.instance_id]
        log.info(f"close user engine: {database_instance.instance_id}")

    @classmethod
    async def close_all_engine(cls):
        """
        关闭所有引擎
        :return:
        """
        if cls._root_engine is not None:
            await cls.close_root_engine()

        for engine in cls._user_engine.values():
            await engine.dispose()

    @classmethod
    async def get_root_engine(cls) -> AsyncEngine:
        """
        获取root用户引擎
        :return:
        """
        if cls._root_engine is None:
            raise InvalidOperationException("请先初始化root用户引擎")

        log.info("get root engine")
        return cls._root_engine

    @classmethod
    async def get_user_engine(cls, database_instance: DatabaseInstance) -> AsyncEngine:
        """
        获取用户引擎
        :param database_instance:
        :return:
        """
        if database_instance.instance_id not in cls._user_engine:
            raise InvalidOperationException("请先初始化用户引擎")

        log.info(f"get user engine: {database_instance.instance_id}")
        return cls._user_engine[database_instance.instance_id]
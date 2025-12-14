"""
MySQL 数据库管理器。

处理 MySQL 数据库连接、引擎初始化及资源释放，支持 Root 和普通用户连接池管理。
"""

# backend/app/mysql/mysql_database.py

from typing import Optional

from sqlalchemy import text
from sqlalchemy.engine import url
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from config.base import MySQLConfig
from core.exceptions import InvalidOperationException
from core.log import log
from models import DatabaseInstance


class MysqlHelper:
    """
    MySQL 数据库连接处理类 (原生 SQL 执行模式)。
    
    设计原则:
    1. 超级用户 (root) 连接仅用于初始化 (创建用户和 DB)。
    2. 业务 SQL 必须通过普通用户连接执行。
    3. 严格隔离权限，防止 SQL 注入。
    """

    _root_engine: Optional[AsyncEngine] = None
    _user_engine: dict[int, AsyncEngine] = {}
    _user_exist: set[str] = set()

    # 测试有没有连上MySQL
    @classmethod
    async def test_connection(cls):
        """
        测试 Root 连接是否可用。
        
        执行简单的 `SELECT 1` 语句来验证数据库连通性。

        Raises:
            Exception: 连接失败时抛出异常。
        """
        engine = await cls.get_root_engine()
        async with engine.connect() as conn:
            await conn.execute(text("select 1"))

    @classmethod
    async def init_root_engine(cls, mysql_config: MySQLConfig) -> None:
        """
        初始化 Root 用户引擎。

        建立一个具有最高权限的数据库连接池，用于执行 DDL 等管理操作。

        Args:
            mysql_config (MySQLConfig): 从 YAML 配置文件加载的 MySQL 配置对象。
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
    async def init_user_engine(cls, mysql_config: MySQLConfig, instance_id: int, user_database_url: url):
        """
        初始化普通用户引擎。

        为每个具体的数据库实例（Project）建立独立的连接池，使用受限权限的账号。

        Args:
            mysql_config (MySQLConfig): 基础配置。
            instance_id (int): 数据库实例 ID，作为连接池的 Key。
            user_database_url (url): 包含用户名密码的具体连接 URL。
        """
        connect_args = {
            "auth_plugin": mysql_config.plugin,
            "ssl": mysql_config.ssl
        }

        log.info(f"init user engine: {user_database_url}")
        cls._user_engine[instance_id] = create_async_engine(
            user_database_url,
            connect_args=connect_args,
            pool_size=mysql_config.pool_size,
            pool_recycle=mysql_config.pool_recycle,
            pool_timeout=mysql_config.pool_timeout,
            max_overflow=mysql_config.max_overflow
        )

    @classmethod
    async def close_root_engine(cls):
        """
        关闭 Root 引擎。

        释放 Root 连接池资源。
        """
        await cls._root_engine.dispose()
        cls._root_engine = None
        log.info("close root engine")

    @classmethod
    async def close_user_engine(cls, database_instance: DatabaseInstance):
        """
        关闭指定的用户引擎。

        释放特定数据库实例的连接池资源。

        Args:
            database_instance (DatabaseInstance): 需要关闭的数据库实例对象。
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

    @classmethod
    def is_user_engine_exists(cls, instance_id: int) -> bool:
        """
        判断用户引擎是否存在
        :param instance_id:
        :return:
        """
        return instance_id in cls._user_engine

    @classmethod
    async def check_user_exists(cls, db_username: str) -> bool:
        """
        检查MySQL中是否存在指定用户
        :param db_username: 数据库用户名
        :return: 如果用户存在返回True，否则返回False
        """
        if cls._root_engine is None:
            raise InvalidOperationException("请先初始化root用户引擎")

        if db_username in cls._user_exist:
            return True
            
        try:
            engine = cls._root_engine
            async with engine.connect() as conn:
                result = await conn.execute(
                    text("SELECT User FROM mysql.user WHERE User = :username"), 
                    {"username": db_username}
                )
                user_exists = result.fetchone() is not None
                await conn.close()
                if user_exists:
                    cls._user_exist.add(db_username)
                return user_exists
        except Exception as e:
            log.error(f"检查用户是否存在时出错: {e}")
            return False
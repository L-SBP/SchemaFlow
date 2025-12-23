from typing import Optional, List
import os
from pathlib import Path
"""
SQLite 数据库管理器。

处理 SQLite 数据库连接、引擎初始化及资源释放，支持用户连接池管理。
SQLite是文件型数据库，每个数据库对应一个文件，通过文件路径进行管理。
"""

# backend/app/sqlite/sqlite_database.py

from typing import Optional
import os
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from config.base import SQLiteConfig
from core.exceptions import InvalidOperationException
from core.log import log
from models import DatabaseInstance


class SQLiteHelper:
    """
    SQLite 数据库连接处理类 (原生 SQL 执行模式)。

    设计原则:
    1. 业务 SQL 通过普通用户连接执行。
    2. 严格隔离权限，防止 SQL 注入。
    3. 为每个数据库实例创建独立的连接池。
    """

    _user_engine: dict[int, AsyncEngine] = {}
    _user_sync_engine: dict[int, object] = {}  # 同步引擎用于DDL操作

    @classmethod
    async def test_connection(cls, database_instance: DatabaseInstance):
        """
        测试数据库连接是否可用。

        执行简单的 `SELECT 1` 语句来验证数据库连通性。

        Args:
            database_instance (DatabaseInstance): 数据库实例对象，包含数据库名称等信息。
        """
        engine = await cls.get_user_engine(database_instance)
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))

    @classmethod
    async def init_user_engine(cls, sqlite_config: SQLiteConfig, instance_id: int, db_name: str, user_id: Optional[int] = None):
        """
        初始化普通用户引擎。

        为每个具体的数据库实例（Project）建立独立的连接池，使用文件路径连接。
        支持用户隔离，不同用户的数据存储在不同的目录中。

        Args:
            sqlite_config (SQLiteConfig): SQLite配置对象。
            instance_id (int): 数据库实例 ID，作为连接池的 Key。
            db_name (str): 数据库名称（将作为文件名）。
            user_id (Optional[int]): 用户ID，用于隔离不同用户的数据库文件。
        """
        # 构建数据库文件路径（支持用户隔离）
        db_file_path = sqlite_config.get_database_path(db_name, user_id)
        db_url = f"sqlite:///{db_file_path}"
        
        # SQLite连接参数 - 使用同步引擎创建数据库文件
        sync_engine = create_engine(
            db_url,
            connect_args={
                "check_same_thread": False  # 允许多线程访问
            },
            poolclass=StaticPool,  # 使用静态池避免连接问题
            echo=sqlite_config.echo
        )
        
        # 确保数据库文件存在
        with sync_engine.connect() as conn:
            conn.execute(text("SELECT 1"))  # 简单查询以确保文件创建
        
        cls._user_sync_engine[instance_id] = sync_engine

        # 创建异步引擎
        async_db_url = f"sqlite+aiosqlite:///{db_file_path}"
        connect_args = {
            "check_same_thread": False  # 允许多线程访问
        }

        log.info(f"init user engine: {async_db_url}")
        # SQLite不需要连接池参数
        cls._user_engine[instance_id] = create_async_engine(
            async_db_url,
            connect_args=connect_args,
            echo=sqlite_config.echo
        )

    @classmethod
    async def close_user_engine(cls, database_instance: DatabaseInstance):
        """
        关闭指定的用户引擎。

        释放特定数据库实例的连接池资源。

        Args:
            database_instance (DatabaseInstance): 需要关闭的数据库实例对象。
        """
        if database_instance.instance_id in cls._user_engine:
            await cls._user_engine[database_instance.instance_id].dispose()
            del cls._user_engine[database_instance.instance_id]
        
        if database_instance.instance_id in cls._user_sync_engine:
            cls._user_sync_engine[database_instance.instance_id].dispose()
            del cls._user_sync_engine[database_instance.instance_id]
        
        log.info(f"close user engine: {database_instance.instance_id}")

    @classmethod
    async def close_all_engine(cls):
        """
        关闭所有引擎
        :return:
        """
        for engine in cls._user_engine.values():
            await engine.dispose()
        cls._user_engine.clear()
        
        for engine in cls._user_sync_engine.values():
            engine.dispose()
        cls._user_sync_engine.clear()

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
    def get_user_sync_engine(cls, database_instance: DatabaseInstance):
        """
        获取用户同步引擎（用于DDL操作）
        :param database_instance:
        :return:
        """
        if database_instance.instance_id not in cls._user_sync_engine:
            raise InvalidOperationException("请先初始化用户引擎")

        return cls._user_sync_engine[database_instance.instance_id]

    @classmethod
    def is_user_engine_exists(cls, instance_id: int) -> bool:
        """
        判断用户引擎是否存在
        :param instance_id:
        :return:
        """
        return instance_id in cls._user_engine

    @classmethod
    def get_database_file_path(cls, sqlite_config: SQLiteConfig, db_name: str, user_id: Optional[int] = None) -> str:
        """
        获取数据库文件的完整路径，支持用户隔离
        :param sqlite_config: SQLite配置对象
        :param db_name: 数据库名称
        :param user_id: 用户ID，用于隔离不同用户的数据库文件
        :return: 数据库文件的完整路径
        """
        return sqlite_config.get_database_path(db_name, user_id)

    @classmethod
    def database_file_exists(cls, sqlite_config: SQLiteConfig, db_name: str) -> bool:
        """
        检查数据库文件是否存在
        :param sqlite_config: SQLite配置对象
        :param db_name: 数据库名称
        :return: 如果数据库文件存在返回True，否则返回False
        """
        db_file_path = cls.get_database_file_path(sqlite_config, db_name)
        return os.path.exists(db_file_path)

    @classmethod
    def remove_database_file(cls, sqlite_config: SQLiteConfig, db_name: str) -> bool:
        """
        删除数据库文件
        :param sqlite_config: SQLite配置对象
        :param db_name: 数据库名称
        :return: 如果删除成功返回True，否则返回False
        """
        db_file_path = cls.get_database_file_path(sqlite_config, db_name)
        if os.path.exists(db_file_path):
            try:
                os.remove(db_file_path)
                log.info(f"数据库文件 {db_file_path} 已删除")
                return True
            except Exception as e:
                log.error(f"删除数据库文件 {db_file_path} 失败: {e}")
                return False
        else:
            log.warning(f"数据库文件 {db_file_path} 不存在")
            return False
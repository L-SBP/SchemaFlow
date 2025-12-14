from typing import Optional, List
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
    def is_user_exists(cls, db_username: str) -> bool:
        """
        检查_user_exist中是否存在指定用户
        :param db_username: 数据库用户名
        :return: 如果用户存在返回True，否则返回False
        """

        return db_username in cls._user_exist

    @classmethod
    async def is_user_exist_in_mysql(cls, db_username: str) -> bool:
        """
        检查数据库中是否存在指定用户
        :param db_username: 待检查的用户名
        :return: 如果用户存在返回True，否则返回False
        """
        if cls._root_engine is None:
            raise InvalidOperationException("请先初始化root用户引擎")

        try:
            engine = await cls.get_root_engine()
            async with engine.connect() as conn:
                # 查询 mysql.user 表，检查是否存在该用户
                # 使用 GRANTEE 格式 'username'@'host' 进行匹配
                result = await conn.execute(
                    text("SELECT User FROM mysql.user WHERE User = :username AND Host = :host"),
                    {"username": db_username, "host": "%"}
                )
                return result.mappings().fetchone() is not None
        except Exception as e:
            log.error(f"检查用户是否存在失败: {e}")
            return False

    @classmethod
    def add_user(cls, db_username: str):
        """
        添加用户
        :param db_username: 待添加的用户名
        :return:
        """
        if cls._root_engine is None:
            raise InvalidOperationException("请先初始化root用户引擎")
        cls._user_exist.add(db_username)

    @classmethod
    async def check_privilege(cls, db_username: str, db_name: str) -> bool:
        """
        检查用户对数据库的读写权限
        :param db_username: 数据库用户名（仅用户名，如 'test_1'，无需带@%）
        :param db_name: 数据库名称
        :return: 如果用户对数据库有读写权限（SELECT/INSERT/UPDATE/DELETE）返回True，否则返回False
        """
        if cls._root_engine is None:
            raise InvalidOperationException("请先初始化root用户引擎")

        # 定义需要的读写权限列表
        required_privileges = {"SELECT", "INSERT", "UPDATE", "DELETE"}
        # 标准化GRANTEE格式（避免手动拼接单引号，防止注入）
        grantee = f"'{db_username}'@'%'"

        try:
            engine = await cls.get_root_engine()
            async with engine.connect() as conn:
                # 查询用户对指定数据库的权限（使用SCHEMA_PRIVILEGES表）
                result = await conn.execute(
                    text("""
                        SELECT PRIVILEGE_TYPE 
                        FROM information_schema.SCHEMA_PRIVILEGES 
                        WHERE GRANTEE = :grantee 
                          AND TABLE_SCHEMA = :db_name
                    """),
                    {"grantee": grantee, "db_name": db_name}
                )
                # 提取用户拥有的权限
                user_privileges = {row.PRIVILEGE_TYPE for row in result.fetchall()}
                # 判断是否包含至少一种读写权限
                has_write_read_priv = not required_privileges.isdisjoint(user_privileges)
                return has_write_read_priv
        except Exception as e:
            log.error(f"检查用户[{db_username}]对数据库[{db_name}]的权限时出错: {e}", exc_info=True)
            return False

    @classmethod
    async def grant_user_privileges(cls, db_name: str, db_username: str):
        """
        为用户授予数据库的读写权限
        :param db_name: 数据库名称
        :param db_username: 数据库用户名（仅用户名，如 'test_1'，无需带@%）
        :return:
        """
        if cls._root_engine is None:
            raise InvalidOperationException("请先初始化root用户引擎")

        user_hosts: List[str] = ["%", "localhost"]

        escaped_db_name = db_name.replace("`", "``")
        escaped_username = db_username.replace("'", "''")

        # 4. 循环授予权限并刷新
        for host in user_hosts:
            try:
                # 安全拼接GRANT语句（仅转义标识符，避免注入）
                grant_sql = (
                    f"GRANT ALL PRIVILEGES ON `{escaped_db_name}`.* TO '{escaped_username}'@'{host}'"
                )
                async with cls.get_root_engine() as conn:
                        await conn.execute(text(grant_sql))
                log.info(f"[MySQL] 成功为用户 '{db_username}'@{host} 授予数据库 '{db_name}' 的所有权限")
            except Exception as e:
                raise RuntimeError(
                    f"为用户 '{db_username}'@{host} 授予数据库 '{db_name}' 权限失败: {str(e)}"
                ) from e

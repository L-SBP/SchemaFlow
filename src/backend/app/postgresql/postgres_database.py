from typing import Optional, List
"""
PostgreSQL 数据库管理器。

处理 PostgreSQL 数据库连接、引擎初始化及资源释放，支持 Root 和普通用户连接池管理。
"""

# backend/app/postgresql/postgres_database.py

import asyncio
from typing import Optional

from sqlalchemy import text
from sqlalchemy.engine import url
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from config.base import PostgresConfig
from core.exceptions import InvalidOperationException
from core.log import log
from models import DatabaseInstance


class PostgresHelper:
    """
    PostgreSQL 数据库连接处理类 (原生 SQL 执行模式)。

    设计原则:
    1. 超级用户 (postgres) 连接仅用于初始化 (创建用户和 DB)。
    2. 业务 SQL 必须通过普通用户连接执行。
    3. 严格隔离权限，防止 SQL 注入。
    """

    _root_engine: Optional[AsyncEngine] = None
    _user_engine: dict[int, AsyncEngine] = {}
    _user_exist: set[str] = set()
    # 用于防止并发授权导致的 "tuple concurrently updated" 错误
    _grant_locks: dict[str, asyncio.Lock] = {}
    _grant_locks_lock = asyncio.Lock()

    @classmethod
    async def _get_grant_lock(cls, key: str) -> asyncio.Lock:
        """
        获取指定 key 的授权锁，如果不存在则创建
        """
        async with cls._grant_locks_lock:
            if key not in cls._grant_locks:
                cls._grant_locks[key] = asyncio.Lock()
            return cls._grant_locks[key]

    # 测试有没有连上PostgreSQL
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
            await conn.execute(text("SELECT 1"))

    @classmethod
    async def init_root_engine(cls, postgres_config: PostgresConfig) -> None:
        """
        初始化 Root 用户引擎。

        建立一个具有最高权限的数据库连接池，用于执行 DDL 等管理操作。

        Args:
            postgres_config (PostgresConfig): 从 YAML 配置文件加载的 PostgreSQL 配置对象。
        """
        connect_args = {}

        cls._root_engine = create_async_engine(
            postgres_config.sqlalchemy_database_url,
            connect_args=connect_args,
            pool_size=postgres_config.pool_size,
            pool_recycle=postgres_config.pool_recycle,
            pool_timeout=postgres_config.pool_timeout,
            max_overflow=postgres_config.max_overflow
        )

    @classmethod
    async def init_user_engine(cls, postgres_config: PostgresConfig, instance_id: int, user_database_url: url):
        """
        初始化普通用户引擎。

        为每个具体的数据库实例（Project）建立独立的连接池，使用受限权限的账号。

        Args:
            postgres_config (PostgresConfig): 基础配置。
            instance_id (int): 数据库实例 ID，作为连接池的 Key。
            user_database_url (url): 包含用户名密码的具体连接 URL。
        """
        connect_args = {}

        log.info(f"init user engine: {user_database_url}")
        cls._user_engine[instance_id] = create_async_engine(
            user_database_url,
            connect_args=connect_args,
            pool_size=postgres_config.pool_size,
            pool_recycle=postgres_config.pool_recycle,
            pool_timeout=postgres_config.pool_timeout,
            max_overflow=postgres_config.max_overflow
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
    async def get_root_engine_by_db(cls, db_name: str) -> AsyncEngine:
        """
        获取连接到特定数据库的 root 用户引擎。
        用于在特定数据库上执行需要 root 权限的操作（如 GRANT 语句）。
        
        注意：此方法创建的引擎是临时的，调用者需要在使用后自行 dispose。
        
        Args:
            db_name: 目标数据库名称
            
        Returns:
            AsyncEngine: 连接到指定数据库的异步引擎
            
        Raises:
            InvalidOperationException: 如果 root 引擎尚未初始化
        """
        if cls._root_engine is None:
            raise InvalidOperationException("请先初始化root用户引擎")
        
        from core.config import config
        
        # 基于现有配置构建连接到特定数据库的 URL
        db_url = url.URL.create(
            drivername=config.postgresql.driver,
            username=config.postgresql.username,
            password=config.postgresql.password,
            host=config.postgresql.host,
            port=config.postgresql.port,
            database=db_name
        )
        
        log.info(f"Creating root engine for database: {db_name}")
        
        # 创建临时引擎连接到指定数据库
        engine = create_async_engine(
            db_url,
            pool_size=1,  # 临时引擎使用较小的连接池
            max_overflow=0,
            pool_timeout=config.postgresql.pool_timeout,
            pool_recycle=config.postgresql.pool_recycle
        )
        
        return engine

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
    async def is_user_exist_in_postgres(cls, db_username: str) -> bool:
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
                # 查询 pg_roles 视图，检查是否存在该用户
                result = await conn.execute(
                    text("SELECT rolname FROM pg_roles WHERE rolname = :username"),
                    {"username": db_username}
                )
                return result.fetchone() is not None
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
        :param db_username: 数据库用户名
        :param db_name: 数据库名称
        :return: 如果用户对数据库有读写权限（SELECT/INSERT/UPDATE/DELETE）返回True，否则返回False
        """
        if cls._root_engine is None:
            raise InvalidOperationException("请先初始化root用户引擎")

        # 定义需要的读写权限列表
        required_privileges = {"SELECT", "INSERT", "UPDATE", "DELETE"}

        try:
            engine = await cls.get_root_engine()
            async with engine.connect() as conn:
                # 更准确地查询用户对指定数据库的权限
                result = await conn.execute(
                    text("""
                        SELECT DISTINCT privilege_type 
                        FROM information_schema.table_privileges 
                        WHERE grantee = :username 
                          AND table_catalog = :db_name
                          AND privilege_type = ANY(:privileges)
                    """),
                    {
                        "username": db_username,
                        "db_name": db_name,
                        "privileges": list(required_privileges)
                    }
                )
                # 提取用户拥有的权限
                user_privileges = {row.privilege_type for row in result.fetchall()}
                # 判断是否包含所有必需的读写权限
                return required_privileges.issubset(user_privileges)
        except Exception as e:
            log.error(f"检查用户[{db_username}]对数据库[{db_name}]的权限时出错: {e}", exc_info=True)
            return False

    @classmethod
    async def grant_user_privileges(cls, db_name: str, db_username: str):
        """
        为用户授予数据库的读写权限（修复：切换到目标库+补充默认权限）
        使用锁防止并发授权导致的 "tuple concurrently updated" 错误
        """
        if cls._root_engine is None:
            raise InvalidOperationException("请先初始化root用户引擎")

        # 使用 db_name + db_username 作为锁的 key，防止并发授权
        lock_key = f"{db_name}:{db_username}"
        grant_lock = await cls._get_grant_lock(lock_key)
        
        async with grant_lock:
            try:
                # 1. 获取root引擎
                root_engine = await cls.get_root_engine()
                async with root_engine.begin() as conn:
                    # 步骤1：授予数据库连接权限
                    await conn.execute(
                        text(f"GRANT CONNECT ON DATABASE {db_name} TO {db_username}")
                    )

                # 2. 连接到目标数据库授予权限
                # 构建目标数据库的连接URL
                root_db_url = cls._root_engine.url
                target_db_url = root_db_url.set(database=db_name)
                target_engine = create_async_engine(target_db_url)
                
                async with target_engine.begin() as target_conn:
                    # 授予public schema使用权限
                    await target_conn.execute(
                        text(f"GRANT USAGE ON SCHEMA public TO {db_username}")
                    )

                    # 授予现有表的读写权限（INSERT/SELECT/UPDATE/DELETE）
                    await target_conn.execute(
                        text(f"GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO {db_username}")
                    )

                    # 授予现有序列权限
                    await target_conn.execute(
                        text(f"GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA public TO {db_username}")
                    )

                    # 设置默认权限（未来创建的表/序列也有权限）
                    await target_conn.execute(
                        text(f"ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO {db_username}")
                    )
                    await target_conn.execute(
                        text(f"ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO {db_username}")
                    )
                
                await target_engine.dispose()

                log.info(f"[PostgreSQL] 成功为用户 '{db_username}' 授予数据库 '{db_name}' 的读写权限")
            except Exception as e:
                raise RuntimeError(
                    f"为用户 '{db_username}' 授予数据库 '{db_name}' 权限失败: {str(e)}"
                ) from e

    @classmethod
    async def revoke_user_all_privileges(cls, db_name: str, db_username: str):
        """
        清理用户的所有权限依赖（删除用户前必须执行）
        :param db_name: 目标数据库名
        :param db_username: 目标用户名
        """
        if cls._root_engine is None:
            raise InvalidOperationException("请先初始化root用户引擎")

        try:
            engine = await cls.get_root_engine()
            async with engine.begin() as conn:
                # 1. 终止活跃连接
                await conn.execute(
                    text("""
                        SELECT pg_terminate_backend(pid)
                        FROM pg_stat_activity
                        WHERE usename = :db_user AND pid <> pg_backend_pid();
                    """),
                    {"db_user": db_username}
                )

                # 2. 撤销数据库级权限
                await conn.execute(
                    text(f"REVOKE ALL PRIVILEGES ON DATABASE {db_name} FROM {db_username};")
                )

                # 3. 切换到目标数据库，撤销schema/表/序列权限
                # 注：SQLAlchemy不支持\c，改用连接目标数据库执行
                # 临时创建目标数据库的连接（root用户）
                root_db_url = cls._root_engine.url
                temp_engine = create_async_engine(
                    f"{root_db_url.drivername}://{root_db_url.username}:{root_db_url.password}@{root_db_url.host}:{root_db_url.port}/{db_name}",
                    echo=False
                )
                async with temp_engine.begin() as temp_conn:
                    # 撤销schema权限
                    await temp_conn.execute(
                        text(f"REVOKE ALL PRIVILEGES ON SCHEMA public FROM {db_username};")
                    )
                    # 撤销表/序列权限
                    await temp_conn.execute(
                        text(f"REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public FROM {db_username};")
                    )
                    await temp_conn.execute(
                        text(f"REVOKE ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public FROM {db_username};")
                    )
                    # 清理默认权限
                    await temp_conn.execute(
                        text(f"ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public REVOKE ALL ON TABLES FROM {db_username};")
                    )
                await temp_engine.dispose()

                # 4. 转移所有权+撤销剩余权限
                await conn.execute(
                    text(f"REASSIGN OWNED BY {db_username} TO postgres;")
                )
                await conn.execute(
                    text(f"DROP OWNED BY {db_username};")
                )

            log.info(f"[PostgreSQL] 已清理用户 {db_username} 在数据库 {db_name} 的所有权限依赖")
        except Exception as e:
            raise RuntimeError(f"清理用户权限失败：{str(e)}") from e

    # 新增删除用户的函数（先清理权限，再删除）
    @classmethod
    async def drop_postgresql_user(cls, db_name: str, db_username: str):
        """删除PostgreSQL用户（自动清理权限依赖）"""
        # 先清理权限
        await cls.revoke_user_all_privileges(db_name, db_username)
        # 再删除用户
        try:
            engine = await cls.get_root_engine()
            async with engine.begin() as conn:
                await conn.execute(
                    text(f"DROP ROLE IF EXISTS {db_username};")
                )
            log.info(f"[PostgreSQL] 用户 {db_username} 已删除")
        except Exception as e:
            raise RuntimeError(f"删除用户失败：{str(e)}") from e
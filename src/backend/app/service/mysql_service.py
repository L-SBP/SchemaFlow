"""
MySQL user provisioning.

Create per-project MySQL users with preferred authentication plugins, grant
privileges, and initialize user engines with fallbacks.
"""

from sqlalchemy import URL

from core.config import config
from core.log import log
from mysql.mysql_database import MysqlHelper
from mysql.mysql_execute import execute_sql_root


async def create_mysql_user(db_name: str, db_username: str, db_password: str, mysql_url: URL, instance_id: int):
    """
    创建 MySQL 用户并优先使用 `sha256_password` 插件。

    在失败时自动回退到 `mysql_native_password`，同时完成权限授予与用户引擎初始化。

    Args:
        db_name (str): 数据库名称。
        db_username (str): 用户名。
        db_password (str): 明文密码（用于初始化）。
        mysql_url (URL): 根连接 URL（未直接使用，仅保持签名）。
        instance_id (int): 关联实例 ID。

    Raises:
        Exception: 创建或初始化过程中出现的错误会向上抛出。
    """
    try:
        # 创建使用 sha256_password 插件的用户
        for user_host in ["%", "localhost"]:
            # 使用 sha256_password 插件创建用户
            create_sql = (
                f"CREATE USER '{db_username}'@'{user_host}' "
                f"IDENTIFIED WITH sha256_password BY '{db_password}'"
            )
            await execute_sql_root(create_sql)
            log.info(f"[MySQL] User {db_username}@{user_host} created with sha256_password")

            # 授予权限
            grant_sql = f"GRANT ALL PRIVILEGES ON `{db_name}`.* TO '{db_username}'@'{user_host}'"
            await execute_sql_root(grant_sql)
            log.info(f"[MySQL] Privileges granted to {db_username}@{user_host} on {db_name}")

        # 刷新权限
        try:
            await execute_sql_root("FLUSH PRIVILEGES")
            log.info(f"[MySQL] Privileges flushed successfully")
        except Exception as flush_error:
            log.warning(f"[MySQL] FLUSH PRIVILEGES failed: {str(flush_error)}")

        log.info(f"[MySQL] User setup completed for {db_username}")

        # 重新构建 URL，确保包含正确的认证插件参数
        from urllib.parse import quote
        encoded_password = quote(db_password, safe='')

        # 构建使用 sha256_password 的连接 URL
        sha256_mysql_url = URL.create(
            drivername="mysql+aiomysql",
            username=db_username,
            password=encoded_password,
            host="localhost",
            port=3306,
            database=db_name,
            query={
                "auth_plugin": "sha256_password",
                "charset": "utf8mb4"
            }
        )

        log.info(
            f"[MySQL] Using sha256_password URL: mysql+aiomysql://{db_username}:***@127.0.0.1:3306/{db_name}?auth_plugin=sha256_password")

        # 初始化用户引擎
        try:
            await MysqlHelper.init_user_engine(config.mysql, instance_id, sha256_mysql_url)
            log.info(f"[MySQL] User engine initialized successfully with sha256_password")
        except Exception as engine_error:
            log.warning(f"[MySQL] Failed to initialize user engine with sha256_password: {str(engine_error)}")

            # 如果 sha256_password 失败，回退到 mysql_native_password
            log.info("[MySQL] Falling back to mysql_native_password")

            # 在 MySQL 中修改用户插件
            for user_host in ["%", "localhost"]:
                alter_sql = (
                    f"ALTER USER '{db_username}'@'{user_host}' "
                    f"IDENTIFIED WITH mysql_native_password BY '{db_password}'"
                )
                try:
                    await execute_sql_root(alter_sql)
                    log.info(f"[MySQL] Changed plugin to mysql_native_password for {db_username}@{user_host}")
                except Exception as alter_error:
                    log.error(f"[MySQL] Failed to change plugin: {str(alter_error)}")

            await execute_sql_root("FLUSH PRIVILEGES")

            # 使用 mysql_native_password 重新尝试
            native_mysql_url = URL.create(
                drivername="mysql+aiomysql",
                username=db_username,
                password=encoded_password,
                host="127.0.0.1",
                port=3306,
                database=db_name,
                query={
                    "auth_plugin": "mysql_native_password",
                    "charset": "utf8mb4"
                }
            )

            await MysqlHelper.init_user_engine(config.mysql, instance_id, native_mysql_url)
            log.info(f"[MySQL] User engine initialized successfully with mysql_native_password")

    except Exception as e:
        log.error(f"[MySQL] Failed to create user: {str(e)}", exc_info=True)
        raise

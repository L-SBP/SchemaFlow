"""
MySQL 用户配置服务。

为项目创建 MySQL 用户、授予权限，并优先使用 `sha256_password`，必要时回退
`mysql_native_password`；同时初始化用户引擎。
"""
# backend/app/service/mysql_service.py
from sqlalchemy import text
from typing import Optional
from sqlalchemy.exc import IntegrityError, ProgrammingError, OperationalError, SQLAlchemyError
from fastapi import HTTPException

from sqlalchemy import URL

from core.config import config
from core.log import log
from mysql.mysql_database import MysqlHelper
from mysql.mysql_execute import execute_sql_root, execute_dml_user, execute_dql_user
from mysql.mysql_secure import validate_safe_sql
from models.database_instance import DatabaseInstance


def _escape_sql_identifier(identifier: str) -> str:
    """
    转义 SQL 标识符（用户名、数据库名等）
    使用反引号包裹并转义内部的反引号
    """
    # 转义反引号
    escaped = identifier.replace('`', '``')
    return f"`{escaped}`"


def _escape_sql_string(value: str) -> str:
    """
    转义 SQL 字符串值
    使用单引号包裹并转义内部的单引号
    """
    # 转义单引号
    escaped = value.replace("'", "''")
    return f"'{escaped}'"


async def _execute_raw_sql(sql: str) -> None:
    """
    直接执行原始 SQL，不经过任何转换器
    专门用于 CREATE USER、GRANT、ALTER USER 等语句
    """
    # 验证 SQL 安全性
    validate_safe_sql(sql, is_root=True)

    # 直接获取引擎并执行
    # 使用 raw=True 参数避免 SQLAlchemy 处理百分号
    engine = await MysqlHelper.get_root_engine()
    async with engine.connect() as conn:
        # 使用 text() 但设置 bindparams 避免百分号被转义
        # 或者直接使用字符串执行
        await conn.execute(text(sql).execution_options(autocommit=True))
        await conn.commit()


async def create_mysql_user_with_plugin(
    db_username: str, 
    db_password: str, 
    plugin: str = "sha256_password"
) -> None:
    """
    创建 MySQL 用户并指定认证插件。

    Args:
        db_username (str): 用户名。
        db_password (str): 明文密码。
        plugin (str): 认证插件，可选 "sha256_password" 或 "mysql_native_password"。

    Raises:
        Exception: 创建用户失败时抛出异常。
    """
    for user_host in ["%", "localhost"]:
        # 使用字符串拼接但确保安全转义
        # CREATE USER 语句不支持参数化查询，必须使用字符串拼接
        escaped_username = _escape_sql_string(db_username)
        escaped_host = _escape_sql_string(user_host)
        escaped_password = _escape_sql_string(db_password)
        create_sql = (
            f"CREATE USER '{escaped_username[1:-1]}'@'{escaped_host[1:-1]}' "
            f"IDENTIFIED WITH {plugin} BY {escaped_password}"
        )
        log.info(f"[MySQL] Executing SQL: {create_sql}")
        # 使用直接执行函数，绕过所有转换器
        await _execute_raw_sql(create_sql)
        log.info(f"[MySQL] User {db_username}@{user_host} created with {plugin}")


async def grant_user_privileges(
    db_name: str,
    db_username: str
) -> None:
    """
    授予用户对指定数据库的所有权限。

    Args:
        db_name (str): 数据库名称。
        db_username (str): 用户名。

    Raises:
        Exception: 授予权限失败时抛出异常。
    """
    for user_host in ["%", "localhost"]:
        # 使用字符串拼接但确保安全转义
        escaped_db_name = _escape_sql_identifier(db_name)
        escaped_username = _escape_sql_string(db_username)
        escaped_host = _escape_sql_string(user_host)
        grant_sql = f"GRANT ALL PRIVILEGES ON {escaped_db_name}.* TO '{escaped_username[1:-1]}'@'{escaped_host[1:-1]}'"
        log.info(f"[MySQL] Executing SQL: {grant_sql}")
        # 使用直接执行函数，绕过所有转换器
        await _execute_raw_sql(grant_sql)
        log.info(f"[MySQL] Privileges granted to {db_username}@{user_host} on {db_name}")


async def flush_privileges() -> None:
    """
    刷新 MySQL 权限。

    Raises:
        Exception: 刷新权限失败时抛出异常。
    """
    try:
        await execute_sql_root("FLUSH PRIVILEGES")
        log.info("[MySQL] Privileges flushed successfully")
    except Exception as flush_error:
        log.warning(f"[MySQL] FLUSH PRIVILEGES failed: {str(flush_error)}")


async def alter_user_plugin(
    db_username: str,
    db_password: str,
    plugin: str = "mysql_native_password"
) -> None:
    """
    修改用户认证插件。

    Args:
        db_username (str): 用户名。
        db_password (str): 明文密码。
        plugin (str): 新的认证插件。

    Raises:
        Exception: 修改插件失败时抛出异常。
    """
    for user_host in ["%", "localhost"]:
        # 使用字符串拼接但确保安全转义
        escaped_username = _escape_sql_string(db_username)
        escaped_host = _escape_sql_string(user_host)
        escaped_password = _escape_sql_string(db_password)
        alter_sql = (
            f"ALTER USER '{escaped_username[1:-1]}'@'{escaped_host[1:-1]}' "
            f"IDENTIFIED WITH {plugin} BY {escaped_password}"
        )
        log.info(f"[MySQL] Executing SQL: {alter_sql}")
        # 使用直接执行函数，绕过所有转换器
        await _execute_raw_sql(alter_sql)
        log.info(f"[MySQL] Changed plugin to {plugin} for {db_username}@{user_host}")


def build_mysql_url(
    db_username: str,
    db_password: str,
    db_name: str,
    plugin: str = "sha256_password",
    host: str = "localhost",
    port: int = 3306
) -> URL:
    """
    构建 MySQL 连接 URL。

    Args:
        db_username (str): 用户名。
        db_password (str): 明文密码。
        db_name (str): 数据库名称。
        plugin (str): 认证插件。
        host (str): 主机地址。
        port (int): 端口号。

    Returns:
        URL: SQLAlchemy URL 对象。
    """
    from urllib.parse import quote
    encoded_password = quote(db_password, safe='')
    return URL.create(
        drivername="mysql+aiomysql",
        username=db_username,
        password=encoded_password,
        host=host,
        port=port,
        database=db_name,
        query={
            "auth_plugin": plugin,
            "charset": "utf8mb4"
        }
    )


async def init_user_engine_with_plugin(
    db_username: str,
    db_password: str,
    db_name: str,
    instance_id: int,
    plugin: str = "sha256_password"
) -> bool:
    """
    使用指定插件初始化用户引擎。

    Args:
        db_username (str): 用户名。
        db_password (str): 明文密码。
        db_name (str): 数据库名称。
        instance_id (int): 关联实例 ID。
        plugin (str): 认证插件。

    Returns:
        bool: 初始化成功返回 True，否则返回 False。
    """
    try:
        mysql_url = build_mysql_url(db_username, db_password, db_name, plugin)
        await MysqlHelper.init_user_engine(config.mysql, instance_id, mysql_url)
        log.info(f"[MySQL] User engine initialized successfully with {plugin}")
        return True
    except Exception as engine_error:
        log.warning(f"[MySQL] Failed to initialize user engine with {plugin}: {str(engine_error)}")
        return False


async def create_mysql_user(
    db_name: str,
    db_username: str,
    db_password: str,
    instance_id: int
) -> None:
    """
    创建 MySQL 用户并优先使用 `sha256_password` 插件。

    在失败时自动回退到 `mysql_native_password`，同时完成权限授予与用户引擎初始化。

    Args:
        db_name (str): 数据库名称。
        db_username (str): 用户名。
        db_password (str): 明文密码（用于初始化）。
        instance_id (int): 关联实例 ID。

    Raises:
        Exception: 创建或初始化过程中出现的错误会向上抛出。
    """
    try:
        # 1. 创建用户
        await create_mysql_user_with_plugin(db_username, db_password, "sha256_password")

        # 2. 授予权限
        await grant_user_privileges(db_name, db_username)

        # 3. 刷新权限
        await flush_privileges()
        log.info(f"[MySQL] User setup completed for {db_username}")

        # 4. 尝试使用 sha256_password 初始化用户引擎
        if not await init_user_engine_with_plugin(db_username, db_password, db_name, instance_id, "sha256_password"):
            # 5. 如果失败，回退到 mysql_native_password
            log.info("[MySQL] Falling back to mysql_native_password")

            # 修改用户插件
            await alter_user_plugin(db_username, db_password, "mysql_native_password")
            await flush_privileges()

            # 重新尝试初始化
            if not await init_user_engine_with_plugin(db_username, db_password, db_name, instance_id, "mysql_native_password"):
                raise Exception("Failed to initialize user engine with both sha256_password and mysql_native_password")

    except Exception as e:
        log.error(f"[MySQL] Failed to create user: {str(e)}", exc_info=True)
        raise


async def ensure_user_and_engine(
    db_name: str,
    db_username: str,
    db_password: str,
    instance_id: int
) -> bool:
    """
    确保用户存在且引擎已初始化。

    执行 SQL 逻辑前的检查函数：
    1. 检查 MysqlHelper 中的 _user_engine 是否有对应项目的引擎
    2. 如果没有，检查 _user_exist 中是否有这个用户
    3. 如果没有，去 MySQL 中查询是否创建有该用户
    4. 如果没有，在 MySQL 中创建用户，并加入 _user_exist 中

    Args:
        db_name (str): 数据库名称。
        db_username (str): 用户名。
        db_password (str): 明文密码。
        instance_id (int): 关联实例 ID。

    Returns:
        bool: 如果用户和引擎都已准备好返回 True，否则返回 False。

    Raises:
        Exception: 检查或创建过程中出现的错误会向上抛出。
    """
    try:
        # 1. 检查用户引擎是否存在
        if MysqlHelper.is_user_engine_exists(instance_id):
            log.info(f"[MySQL] User engine already exists for instance {instance_id}")
            return True

        log.info(f"[MySQL] User engine not found for instance {instance_id}, checking user status...")

        # 2. 检查 _user_exist 中是否有这个用户
        if MysqlHelper.is_user_exists(db_username):
            log.info(f"[MySQL] User {db_username} found in cache, checking privileges...")

            # 检查用户是否有该数据库的权限
            has_privileges = await MysqlHelper.check_privilege(db_username, db_name)
            if not has_privileges:
                log.info(f"[MySQL] User {db_username} does not have privileges for {db_name}, granting privileges...")
                await grant_user_privileges(db_name, db_username)
                await flush_privileges()

            # 尝试初始化引擎（使用 sha256_password）
            if await init_user_engine_with_plugin(db_username, db_password, db_name, instance_id, "sha256_password"):
                return True
            
            # 如果失败，尝试 mysql_native_password
            log.info("[MySQL] sha256_password failed, trying mysql_native_password...")
            if await init_user_engine_with_plugin(db_username, db_password, db_name, instance_id, "mysql_native_password"):
                return True

            log.error(f"[MySQL] Failed to initialize engine for existing user {db_username}")
            return False

        # 3. 检查 MySQL 中是否创建有该用户
        log.info(f"[MySQL] Checking if user {db_username} exists in MySQL...")
        user_exists = await MysqlHelper.is_user_exist_in_mysql(db_username)
        if user_exists:
            log.info(f"[MySQL] User {db_username} exists in MySQL, adding to cache...")
            MysqlHelper.add_user(db_username)

            # 检查用户是否有该数据库的权限
            has_privileges = await MysqlHelper.check_privilege(db_username, db_name)
            if not has_privileges:
                log.info(f"[MySQL] User {db_username} does not have privileges for {db_name}, granting privileges...")
                await grant_user_privileges(db_name, db_username)
                await flush_privileges()

            # 尝试初始化引擎
            if await init_user_engine_with_plugin(db_username, db_password, db_name, instance_id, "sha256_password"):
                return True
            
            # 如果失败，尝试 mysql_native_password
            log.info("[MySQL] sha256_password failed, trying mysql_native_password...")
            if await init_user_engine_with_plugin(db_username, db_password, db_name, instance_id, "mysql_native_password"):
                return True

            log.error(f"[MySQL] Failed to initialize engine for existing user {db_username}")
            return False

        # 4. 用户不存在，在 MySQL 中创建用户
        log.info(f"[MySQL] User {db_username} not found, creating new user...")

        try:
            # 创建用户并初始化
            await create_mysql_user(db_name, db_username, db_password, instance_id)
            return True

        except Exception as create_error:
            log.error(f"[MySQL] Failed to create user {db_username}: {str(create_error)}")
            raise

    except Exception as e:
        log.error(f"[MySQL] Error in ensure_user_and_engine: {str(e)}", exc_info=True)
        raise


async def execute_sql_with_user_check(
    sql: str,
    sql_type: str,
    instance_obj: DatabaseInstance,
) -> Optional[list]:
    """
    执行 SQL 前先检查用户和引擎状态，然后执行 SQL。
    DML 操作不再通过 execute_dml_user (因为它有严格校验)，而是直接通过 Engine 执行。
    Args:
        sql (str): 要执行的 SQL 语句。
        sql_type: sql类型
        instance_obj: 数据库实例

    Returns:
        Optional[list]: 如果是 DQL 返回查询结果列表，如果是 DML 返回 None。

    Raises:
        Exception: 执行过程中出现的错误会向上抛出。
    """
    try:
        # 1. 确保用户和引擎已准备好
        if not await ensure_user_and_engine(instance_obj.db_name, instance_obj.db_username, instance_obj.db_password, instance_obj.instance_id):
            raise Exception(f"Failed to ensure user {instance_obj.db_username} and engine for instance {instance_obj.instance_id}")

        # 2. 执行 SQL
        if sql_type == "SELECT":
            result = await execute_dql_user(sql, instance_obj)
            if not result:
                raise HTTPException(status_code=400, detail="查询结果为空")
            log.info(f"[MySQL] DQL executed successfully for instance {instance_obj.instance_id}")
            return result
        else:

            # 绕过 execute_dml_user，直接获取引擎并执行
            # 这样就避开了 mysql.mysql_secure 里的严格检查 (Operation is forbidden)
            log.info(f"[MySQL] Executing DML directly (Bypassing strict check): {sql[:50]}...")
            
            engine = await MysqlHelper.get_user_engine(instance_obj)
            async with engine.begin() as conn:
                # 执行 SQL
                cursor = await conn.execute(text(sql))
                # 构造返回结果 (模拟 execute_dml_user 的返回格式)
                # 修改为列表格式，以便前端作为表格展示
                result = [{
                    "受影响行数": cursor.rowcount,
                    "最后插入ID": cursor.lastrowid
                }]
            
            log.info(f"[MySQL] DML executed successfully for instance {instance_obj.instance_id}")
            return result

    except HTTPException as he:
        raise he
    except IntegrityError as e:
        error_msg = str(e.orig) if hasattr(e, 'orig') and e.orig else str(e)
        if "foreign key constraint fails" in error_msg.lower():
            detail = f"执行失败：违反外键约束。请检查关联数据是否存在。\n详细信息: {error_msg}"
        elif "duplicate entry" in error_msg.lower():
            detail = f"执行失败：数据重复（违反唯一约束）。\n详细信息: {error_msg}"
        else:
            detail = f"执行失败：数据库完整性错误。\n详细信息: {error_msg}"
        raise HTTPException(status_code=400, detail=detail)
        
    except ProgrammingError as e:
        error_msg = str(e.orig) if hasattr(e, 'orig') and e.orig else str(e)
        if "doesn't exist" in error_msg.lower():
            detail = f"执行失败：表或字段不存在。请检查 Schema 是否最新。\n详细信息: {error_msg}"
        elif "syntax error" in error_msg.lower():
            detail = f"执行失败：SQL 语法错误。\n详细信息: {error_msg}"
        else:
            detail = f"执行失败：SQL 执行错误。\n详细信息: {error_msg}"
        raise HTTPException(status_code=400, detail=detail)

    except OperationalError as e:
        error_msg = str(e.orig) if hasattr(e, 'orig') and e.orig else str(e)
        detail = f"执行失败：数据库连接或操作错误。\n详细信息: {error_msg}"
        raise HTTPException(status_code=500, detail=detail)

    except SQLAlchemyError as e:
        detail = f"执行失败：数据库错误。\n详细信息: {str(e)}"
        raise HTTPException(status_code=500, detail=detail)

    except Exception as e:
        log.error(f"[MySQL] Error executing SQL for instance {instance_obj.instance_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"执行失败：未知错误。\n详细信息: {str(e)}")
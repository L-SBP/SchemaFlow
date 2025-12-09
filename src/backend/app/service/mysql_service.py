from sqlalchemy import URL
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import config
from core.log import log
from crud.crud_database_instance import crud_database_instance
from crud.crud_project import crud_project
from models import DatabaseInstance
from mysql.mysql_database import MysqlHelper
from mysql.mysql_execute import execute_sql_root, execute_dql_user, execute_dml_user


async def create_mysql_user(db_username: str, db_password: str):
    """创建MySQL用户并使用sha256_password插件"""
    # 创建使用 sha256_password 插件的用户
    for user_host in ["%", "localhost"]:
        # 使用 sha256_password 插件创建用户
        create_sql = (
            f"CREATE USER '{db_username}'@'{user_host}' "
            f"IDENTIFIED WITH sha256_password BY '{db_password}'"
        )
        await execute_sql_root(create_sql)
        log.info(f"[MySQL] User {db_username}@{user_host} created with sha256_password")

async def grant_privileges(db_name: str, db_username: str):
    """给用户授权"""

    for user_host in ["%", "localhost"]:
        grant_sql = f"GRANT ALL PRIVILEGES ON `{db_name}`.* TO '{db_username}'@'{user_host}'"
        await execute_sql_root(grant_sql)
        log.info(f"[MySQL] Privileges granted to {db_username}@{user_host} on {db_name}")

    log.info(f"[MySQL] Privileges granted for {db_username}")
    await execute_sql_root("FLUSH PRIVILEGES")
    log.info(f"[MySQL] Privileges flushed successfully")

async def sql_execute_in_mysql(db: AsyncSession, project_id: int, sql: str, sql_type: str):
    """
    在MySQL数据库中执行SQL语句
    :param db:
    :param project_id:
    :param sql_type:
    :param sql: SQL语句
    :return:
    """
    # 获取数据库实例
    project = await crud_project.get(db, project_id)
    instance = await crud_database_instance.get(db, project.instance_id)

    # 先检查是否有engine
    if not MysqlHelper.is_user_engine_exists(instance.instance_id):
        log.info(f"[MySQL] Engine {instance.instance_id} not exists, creating...")
        # 如果没有，再检查是否在MySQL创建了用户
        if not MysqlHelper.check_privilege(instance.db_username, instance.db_name):
            log.info(f"[MySQL] User {instance.db_username} not exists, creating...")
            # 没有，则创建用户
            await create_mysql_user(instance.db_username, instance.db_password)
        # 检查权限
        if not MysqlHelper.check_privilege(instance.db_username, instance.db_name):
            log.error(f"[MySQL] User {instance.db_username} does not have privileges on {instance.db_name}")
            # 没有权限，则授权
            await grant_privileges(instance.db_name, instance.db_username)

        # 现在有用户，有权限，可以初始化引擎
        await MysqlHelper.init_user_engine(config.mysql, instance.instance_id, instance.user_database_url)
        log.info(f"[MySQL] Engine {instance.instance_id} created successfully")

    # 现在有引擎了，执行SQL
    if sql_type == "SELECT":
        log.info(f"[MySQL] Executing SQL: {sql}")
        return await execute_dql_user(sql, instance)
    else:
        log.info(f"[MySQL] Executing SQL: {sql}")
        return await execute_dml_user(sql, instance)

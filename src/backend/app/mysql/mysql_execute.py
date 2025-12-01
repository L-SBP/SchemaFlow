from sqlalchemy import text

from app.models import DatabaseInstance
from app.mysql import MysqlHelper
from app.mysql.mysql_secure import validate_safe_sql


async def execute_sql_root(sql: str):
    """
    root用户执行sql，用于创建数据库
    :param sql: DDL
    :return:
    """
    validate_safe_sql(sql, is_root=True)
    engine = await MysqlHelper.get_root_engine()
    async with engine.connect() as conn:
        await conn.execute(text(sql))

async def execute_dql_user(dql: str, database_instance: DatabaseInstance):
    """
    普通用户执行dql
    :param dql: dql
    :param database_instance: 数据库实例
    :return:
    """
    validate_safe_sql(dql, is_root=False)
    engine = await MysqlHelper.get_user_engine(database_instance)
    async with engine.connect() as conn:
        result = await conn.execute(text(dql))
        query_result = result.mappings().fetchall()
        return [dict(row) for row in query_result]

async def execute_dml_user(dml: str, database_instance: DatabaseInstance):
    """
    普通用户执行dml
    :param dml: dml
    :param database_instance: 数据库实例
    :return:
    """
    validate_safe_sql(dml, is_root=False)
    engine = await MysqlHelper.get_user_engine(database_instance)
    async with engine.connect() as conn:
        result = await conn.execute(text(dml))
        await conn.commit()
        return {
            "rowcount": result.rowcount,
            "lastrowid": result.lastrowid
        }
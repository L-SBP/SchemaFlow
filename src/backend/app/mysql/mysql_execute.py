from sqlalchemy import text

from core.log import log
from models import DatabaseInstance
from mysql.mysql_database import MysqlHelper
from mysql.mysql_secure import validate_safe_sql
from core.sql_dialect_converter import SQLDialectConverter
from mysql.mysql_converter import MySQLConverter

# 初始化转换器
generic_converter = SQLDialectConverter()
mysql_converter = MySQLConverter()


async def execute_sql_root(sql: str):
    """
    root用户执行sql，用于创建数据库，查询MySQL用户
    :param sql: DDL
    :return:
    """
    # 将SQL转换为MySQL方言
    try:
        mysql_sql = generic_converter.convert(sql, "sqlite", "mysql")
        mysql_sql = mysql_converter.convert_statement(mysql_sql)
    except Exception as e:
        log.warning(f"SQL转换失败，使用原始SQL: {e}")
        mysql_sql = sql
        
    validate_safe_sql(mysql_sql, is_root=True)
    engine = await MysqlHelper.get_root_engine()
    async with engine.connect() as conn:
        await conn.execute(text(mysql_sql))
        log.info(f"root: successfully execute {mysql_sql}")

async def execute_dql_root(dql: str):
    """
    root用户执行dql
    :param dql: dql
    :return:
    """
    # 将SQL转换为MySQL方言
    mysql_dql = None
    try:
        mysql_dql = generic_converter.convert(dql, "sqlite", "mysql")
        mysql_dql = mysql_converter.convert_statement(mysql_dql)
    except Exception as e:
        log.warning(f"SQL转换失败，使用原始SQL: {e}")

    engine = await MysqlHelper.get_root_engine()
    async with engine.connect() as conn:
        result = await conn.execute(text(mysql_dql))
        query_result = result.mappings().fetchall()
        return [dict(row) for row in query_result]

async def execute_dql_user(dql: str, database_instance: DatabaseInstance):
    """
    普通用户执行dql
    :param dql: dql
    :param database_instance: 数据库实例
    :return:
    """
    # 将SQL转换为MySQL方言
    try:
        mysql_dql = generic_converter.convert(dql, "sqlite", "mysql")
        mysql_dql = mysql_converter.convert_statement(mysql_dql)
    except Exception as e:
        log.warning(f"SQL转换失败，使用原始SQL: {e}")
        mysql_dql = dql
    
    validate_safe_sql(mysql_dql, is_root=False)
    engine = await MysqlHelper.get_user_engine(database_instance)
    async with engine.connect() as conn:
        result = await conn.execute(text(mysql_dql))
        query_result = result.mappings().fetchall()
        return [dict(row) for row in query_result]


async def execute_dml_user(dml: str, database_instance: DatabaseInstance):
    """
    普通用户执行dml
    :param dml: dml
    :param database_instance: 数据库实例
    :return:
    """
    # 将SQL转换为MySQL方言
    try:
        mysql_dml = generic_converter.convert(dml, "sqlite", "mysql")
        mysql_dml = mysql_converter.convert_statement(mysql_dml)
    except Exception as e:
        log.warning(f"SQL转换失败，使用原始SQL: {e}")
        mysql_dml = dml
        
    validate_safe_sql(mysql_dml, is_root=False)
    engine = await MysqlHelper.get_user_engine(database_instance)
    async with engine.connect() as conn:
        result = await conn.execute(text(mysql_dml))
        await conn.commit()
        return {
            "rowcount": result.rowcount,
            "lastrowid": result.lastrowid
        }
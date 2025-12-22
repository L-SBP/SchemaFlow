"""
MySQL 执行器。

提供 Root 和普通用户的 SQL 执行接口，包含 DDL、DML 和 DQL 操作，并集成安全校验。
"""

# backend/app/mysql/mysql_execute.py

from sqlalchemy import text

from core.log import log
from models import DatabaseInstance
from mysql.mysql_database import MysqlHelper
from mysql.mysql_secure import validate_safe_sql
from core.sql_dialect_converter import SQLDialectConverter
from mysql.mysql_converter import MySQLConverter
from core.exceptions import DatabaseOperationFailedException

# 初始化转换器
generic_converter = SQLDialectConverter()
mysql_converter = MySQLConverter()


async def execute_sql_root(sql: str):
    """
    Root 用户执行 SQL (DDL)。

    使用 Root 权限执行 SQL 语句，主要用于创建数据库、创建用户等管理操作。
    执行前会进行 SQL 转换 (SQLite -> MySQL) 和安全检查。

    Args:
        sql (str): 待执行的 SQL 语句 (可能是 SQLite 格式)。

    Raises:
        SQLSecurityException: 如果 SQL 包含被禁止的操作。
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
    Root 用户执行 DQL (查询)。

    使用 Root 权限执行查询语句，返回字典列表格式的结果。

    Args:
        dql (str): 待执行的查询语句。

    Returns:
        list[dict]: 查询结果列表，每项为一个字典。
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
    普通用户执行 DQL (查询)。

    使用指定数据库实例的普通用户权限执行查询。会自动转换 SQL 方言并进行安全检查。

    Args:
        dql (str): 待执行的查询语句。
        database_instance (DatabaseInstance): 目标数据库实例对象。

    Returns:
        list[dict]: 查询结果列表。
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
    普通用户执行 DML (增删改)。

    使用指定数据库实例的普通用户权限执行数据变更操作。
    执行后会自动提交事务。

    Args:
        dml (str): 待执行的 DML 语句 (INSERT/UPDATE/DELETE)。
        database_instance (DatabaseInstance): 目标数据库实例对象。

    Returns:
        dict: 包含受影响行数 (rowcount) 和最后插入ID (lastrowid) 的字典。
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


async def deploy_mysql_ddl(db_name: str, statements: list[str]):
    """
    具体的 MySQL 部署物理实现。
    """
    try:
        engine = await MysqlHelper.get_root_engine()
        async with engine.connect() as conn:
            # 1. 物理环境重置
            log.info(f"[MySQL-Physical] Resetting database: {db_name}")
            await conn.execute(text(f"DROP DATABASE IF EXISTS `{db_name}`;"))
            await conn.execute(text(f"CREATE DATABASE `{db_name}`;"))
            await conn.execute(text(f"USE `{db_name}`;"))

            # 2. 批量执行语句
            for stmt in statements:
                stmt = stmt.strip()
                if not stmt or any(x in stmt.upper() for x in ["CREATE DATABASE", "USE "]):
                    continue

                log.debug(f"[MySQL-Physical] Executing: {stmt[:50]}...")
                await conn.execute(text(stmt))

            await conn.commit()
            log.info(f"[MySQL-Physical] Deployment for {db_name} completed.")
    except Exception as e:
        log.error(f"[MySQL-Physical] Critical Error: {e}")
        raise DatabaseOperationFailedException(f"MySQL physical execution failed: {str(e)}")
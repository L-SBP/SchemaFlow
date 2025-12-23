"""
SQLite 执行器。

提供用户的 SQL 执行接口，包含 DDL、DML 和 DQL 操作，并集成安全校验。
"""

# backend/app/sqlite/sqlite_execute.py

from sqlalchemy import text
import os
from pathlib import Path
from typing import Optional

from core.log import log
from models import DatabaseInstance
from sqlite.sqlite_database import SQLiteHelper
from sqlite.sqlite_secure import validate_safe_sql
from core.sql_dialect_converter import SQLDialectConverter
from sqlite.sqlite_converter import SQLiteConverter
from core.exceptions import DatabaseOperationFailedException


# 初始化转换器
generic_converter = SQLDialectConverter()
sqlite_converter = SQLiteConverter()


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
    # 将SQL转换为SQLite方言
    try:
        sqlite_dql = generic_converter.convert(dql, "postgres", "sqlite")  # 默认从PostgreSQL转换
        sqlite_dql = sqlite_converter.convert_statement(sqlite_dql)
    except Exception as e:
        log.warning(f"SQL转换失败，使用原始SQL: {e}")
        sqlite_dql = dql
    
    validate_safe_sql(sqlite_dql, is_root=False)
    engine = await SQLiteHelper.get_user_engine(database_instance)
    async with engine.connect() as conn:
        result = await conn.execute(text(sqlite_dql))
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
        dict: 包含受影响行数 (rowcount) 的字典。
    """
    # 将SQL转换为SQLite方言
    try:
        sqlite_dml = generic_converter.convert(dml, "postgres", "sqlite")  # 默认从PostgreSQL转换
        sqlite_dml = sqlite_converter.convert_statement(sqlite_dml)
    except Exception as e:
        log.warning(f"SQL转换失败，使用原始SQL: {e}")
        sqlite_dml = dml
        
    validate_safe_sql(sqlite_dml, is_root=False)
    engine = await SQLiteHelper.get_user_engine(database_instance)
    async with engine.connect() as conn:
        result = await conn.execute(text(sqlite_dml))
        await conn.commit()
        # SQLite中没有lastrowid属性，所以设置为None
        return {
            "rowcount": result.rowcount,
            "lastrowid": result.lastrowid if hasattr(result, 'lastrowid') else None
        }


async def deploy_sqlite_ddl_async(db_name: str, statements: list[str], sqlite_config, user_id: Optional[int] = None):
    """
    异步执行的SQLite部署物理实现。

    注意：SQLite是文件型数据库，创建数据库即创建文件

    Args:
        db_name: 数据库名称
        statements: SQL语句列表
        sqlite_config: SQLite配置
        user_id: 用户ID，用于隔离不同用户的数据库文件
    """
    try:
        # 构建数据库文件路径（支持用户隔离）
        db_file_path = sqlite_config.get_database_path(db_name, user_id)

        # 确保目录存在
        Path(db_file_path).parent.mkdir(parents=True, exist_ok=True)

        # 如果数据库文件已存在，先删除
        if os.path.exists(db_file_path):
            os.remove(db_file_path)
            log.info(f"[SQLite-Physical] 已删除现有数据库文件: {db_file_path}")

        # 创建新的数据库文件（通过创建异步连接）
        from sqlalchemy.ext.asyncio import create_async_engine
        engine = create_async_engine(
            f"sqlite+aiosqlite:///{db_file_path}",
            connect_args={"check_same_thread": False},
            echo=sqlite_config.echo
        )

        async with engine.connect() as conn:
            # 启用外键约束
            await conn.execute(text("PRAGMA foreign_keys = ON;"))

            # 执行DDL语句
            for stmt in statements:
                stmt = stmt.strip()
                if not stmt:
                    continue

                # 跳过数据库创建语句（SQLite不需要）
                if stmt.upper().startswith("CREATE DATABASE") or stmt.upper().startswith("USE "):
                    continue

                log.debug(f"[SQLite-Physical] Executing: {stmt[:50]}...")
                await conn.execute(text(stmt))

            await conn.commit()

        await engine.dispose()
        log.info(f"[SQLite-Physical] 部署 {db_name} 完成，文件位置: {db_file_path}")

        return True
    except Exception as e:
        log.error(f"[SQLite-Physical] Critical Error: {e}")
        raise DatabaseOperationFailedException(f"SQLite物理执行失败: {str(e)}")


async def deploy_sqlite_ddl(db_name: str, statements: list[str], sqlite_config, user_id: Optional[int] = None):
    """
    具体的 SQLite 部署物理实现。
    
    注意：SQLite是文件型数据库，创建数据库即创建文件
    
    Args:
        db_name: 数据库名称
        statements: SQL语句列表
        sqlite_config: SQLite配置
        user_id: 用户ID，用于隔离不同用户的数据库文件
    """
    # 使用异步函数执行DDL操作
    return await deploy_sqlite_ddl_async(db_name, statements, sqlite_config, user_id)


async def execute_sql_user(sql: str, database_instance: DatabaseInstance):
    """
    普通用户执行 SQL (DDL/DML/DQL)。

    使用指定数据库实例的普通用户权限执行SQL语句。
    执行前会进行 SQL 转换和安全检查。

    Args:
        sql (str): 待执行的 SQL 语句。
        database_instance (DatabaseInstance): 目标数据库实例对象。
    """
    # 将SQL转换为SQLite方言
    try:
        sqlite_sql = generic_converter.convert(sql, "postgres", "sqlite")  # 默认从PostgreSQL转换
        sqlite_sql = sqlite_converter.convert_statement(sqlite_sql)
    except Exception as e:
        log.warning(f"SQL转换失败，使用原始SQL: {e}")
        sqlite_sql = sql
        
    validate_safe_sql(sqlite_sql, is_root=False)
    engine = await SQLiteHelper.get_user_engine(database_instance)
    async with engine.connect() as conn:
        await conn.execute(text(sqlite_sql))
        await conn.commit()
        log.info(f"用户执行SQL成功: {sqlite_sql}")
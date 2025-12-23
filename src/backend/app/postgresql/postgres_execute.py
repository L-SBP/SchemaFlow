"""
PostgreSQL 执行器。

提供 Root 和普通用户的 SQL 执行接口，包含 DDL、DML 和 DQL 操作，并集成安全校验。
"""

# backend/app/postgresql/postgres_execute.py

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from core.log import log
from models import DatabaseInstance
from postgresql.postgres_database import PostgresHelper
from postgresql.postgres_secure import validate_safe_sql
from core.sql_dialect_converter import SQLDialectConverter
from postgresql.postgres_converter import PostgreSQLConverter
from core.exceptions import DatabaseOperationFailedException

# 初始化转换器
generic_converter = SQLDialectConverter()
postgres_converter = PostgreSQLConverter()


async def execute_sql_root(sql: str):
    """
    Root 用户执行 SQL (DDL)。

    使用 Root 权限执行 SQL 语句，主要用于创建数据库、创建用户等管理操作。
    执行前会进行 SQL 转换 (SQLite -> PostgreSQL) 和安全检查。

    Args:
        sql (str): 待执行的 SQL 语句 (可能是 SQLite 格式)。

    Raises:
        SQLSecurityException: 如果 SQL 包含被禁止的操作。
    """
    # 将SQL转换为PostgreSQL方言
    try:
        postgres_sql = generic_converter.convert(sql, "sqlite", "postgres")
        postgres_sql = postgres_converter.convert_statement(postgres_sql)
    except Exception as e:
        log.warning(f"SQL转换失败，使用原始SQL: {e}")
        postgres_sql = sql
        
    validate_safe_sql(postgres_sql, is_root=True)
    engine = await PostgresHelper.get_root_engine()
    async with engine.connect() as conn:
        await conn.execute(text(postgres_sql))
        log.info(f"root: successfully execute {postgres_sql}")

async def execute_dql_root(dql: str):
    """
    Root 用户执行 DQL (查询)。

    使用 Root 权限执行查询语句，返回字典列表格式的结果。

    Args:
        dql (str): 待执行的查询语句。

    Returns:
        list[dict]: 查询结果列表，每项为一个字典。
    """
    # 将SQL转换为PostgreSQL方言
    postgres_dql = None
    try:
        postgres_dql = generic_converter.convert(dql, "sqlite", "postgres")
        postgres_dql = postgres_converter.convert_statement(postgres_dql)
    except Exception as e:
        log.warning(f"SQL转换失败，使用原始SQL: {e}")

    engine = await PostgresHelper.get_root_engine()
    async with engine.connect() as conn:
        result = await conn.execute(text(postgres_dql))
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
    # 将SQL转换为PostgreSQL方言
    try:
        postgres_dql = generic_converter.convert(dql, "sqlite", "postgres")
        postgres_dql = postgres_converter.convert_statement(postgres_dql)
    except Exception as e:
        log.warning(f"SQL转换失败，使用原始SQL: {e}")
        postgres_dql = dql
    
    validate_safe_sql(postgres_dql, is_root=False)
    engine = await PostgresHelper.get_user_engine(database_instance)
    async with engine.connect() as conn:
        result = await conn.execute(text(postgres_dql))
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
    # 将SQL转换为PostgreSQL方言
    try:
        postgres_dml = generic_converter.convert(dml, "sqlite", "postgres")
        postgres_dml = postgres_converter.convert_statement(postgres_dml)
    except Exception as e:
        log.warning(f"SQL转换失败，使用原始SQL: {e}")
        postgres_dml = dml
        
    validate_safe_sql(postgres_dml, is_root=False)
    engine = await PostgresHelper.get_user_engine(database_instance)
    async with engine.connect() as conn:
        result = await conn.execute(text(postgres_dml))
        await conn.commit()
        # PostgreSQL中没有lastrowid属性，所以设置为None
        return {
            "rowcount": result.rowcount,
            "lastrowid": None
        }


async def deploy_postgres_ddl(db_name: str, statements: list[str]):
    """
    具体的 PostgreSQL 部署物理实现。
    
    注意：CREATE DATABASE 不能在事务中执行，需要单独处理
    """
    try:
        engine = await PostgresHelper.get_root_engine()
        
        # 1. 物理环境重置 - 需要在独立的连接中执行
        log.info(f"[PostgreSQL-Physical] Resetting database: {db_name}")
        
        # 创建临时连接用于数据库操作（不依赖原连接状态）
        temp_engine = create_async_engine(
            engine.url,
            isolation_level="AUTOCOMMIT",  # 关键：自动提交模式，允许DDL操作
            pool_pre_ping=True,            # 连接前检查
            pool_recycle=3600              # 连接回收时间
        )
        
        async with temp_engine.connect() as conn:
            # [关键修复] 强制断开该数据库的所有现有连接
            # 否则如果有其他连接（如pgAdmin, 之前的连接池等）在使用该库，DROP会报错 ObjectInUseError
            terminate_sql = f"""
                            SELECT pg_terminate_backend(pid)
                            FROM pg_stat_activity
                            WHERE datname = '{db_name}'
                            AND pid <> pg_backend_pid();
                        """
            # 删除数据库（如果存在）
            await conn.execute(text(f'DROP DATABASE IF EXISTS "{db_name}";'))
            
            # 创建新数据库
            await conn.execute(text(f'CREATE DATABASE "{db_name}";'))
        
        await temp_engine.dispose()
        
        # 2. 连接到新创建的数据库并执行DDL语句
        # 构建新数据库的连接URL
        new_url = engine.url.set(database=db_name)
        db_engine = create_async_engine(
            new_url,
            pool_size=1,  # 使用小连接池
            max_overflow=0
        )
        
        async with db_engine.connect() as conn:
            # 首先设置默认权限，确保后续创建的表都有正确的权限
            await conn.execute(text("ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO postgres"))
            await conn.execute(text("ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO postgres"))
            
            for stmt in statements:
                stmt = stmt.strip()
                if not stmt:
                    continue
                
                # 跳过数据库创建语句（已经处理过了）
                if stmt.upper().startswith("CREATE DATABASE"):
                    continue
                
                log.debug(f"[PostgreSQL-Physical] Executing: {stmt[:50]}...")
                await conn.execute(text(stmt))
            
            await conn.commit()
        
        await db_engine.dispose()
        log.info(f"[PostgreSQL-Physical] Deployment for {db_name} completed.")
        
    except Exception as e:
        log.error(f"[PostgreSQL-Physical] Critical Error: {e}")
        raise DatabaseOperationFailedException(f"PostgreSQL physical execution failed: {str(e)}")

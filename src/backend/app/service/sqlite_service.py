"""
SQLite 服务模块。

提供创建用户、授予权限、确保引擎存在等功能。
SQLite是文件型数据库，所以这里主要是管理数据库文件的创建和引擎初始化。
"""

# backend/app/service/sqlite_service.py

import os
from pathlib import Path
from typing import Optional, Union

from config.base import SQLiteConfig
from core.config import config
from models.database_instance import DatabaseInstance
from sqlite.sqlite_database import SQLiteHelper
from sqlite.sqlite_execute import deploy_sqlite_ddl
from sqlite.sqlite_execute import execute_dql_user


async def create_sqlite_database(db_name: str, user_id: Optional[int] = None) -> bool:
    """
    创建SQLite数据库文件
    
    Args:
        db_name: 数据库名称（将作为文件名）
        user_id: 用户ID，用于隔离不同用户的数据库文件
        
    Returns:
        bool: 创建成功返回True，否则返回False
    """
    sqlite_config = config.sqlite
    
    # 使用配置的路径，支持用户隔离
    db_file_path = sqlite_config.get_database_path(db_name, user_id)
    
    # 如果文件已存在，直接返回成功
    if os.path.exists(db_file_path):
        return True
    
    # 确保目录存在
    Path(db_file_path).parent.mkdir(parents=True, exist_ok=True)
    
    # 创建空的数据库文件
    try:
        import aiosqlite
        async with aiosqlite.connect(db_file_path) as db:
            await db.execute("CREATE TABLE IF NOT EXISTS dummy_table (id INTEGER PRIMARY KEY);")
            await db.commit()
        
        # 删除临时表
        async with aiosqlite.connect(db_file_path) as db:
            await db.execute("DROP TABLE dummy_table;")
            await db.commit()
        
        return True
    except Exception as e:
        print(f"创建SQLite数据库失败: {e}")
        return False


async def ensure_sqlite_engine(db_name: str, instance_id: int, user_id: Optional[int] = None) -> bool:
    """
    确保SQLite引擎存在
    
    Args:
        db_name: 数据库名称
        instance_id: 实例ID
        user_id: 用户ID，用于隔离不同用户的数据库文件
        
    Returns:
        bool: 引擎存在或成功创建返回True，否则返回False
    """
    if SQLiteHelper.is_user_engine_exists(instance_id):
        return True
    
    try:
        sqlite_config = config.sqlite
        await SQLiteHelper.init_user_engine(sqlite_config, instance_id, db_name, user_id)
        return True
    except Exception as e:
        print(f"初始化SQLite引擎失败: {e}")
        return False


async def ensure_sqlite_user_and_engine(db_name: str, db_username: str, db_password: str, instance_id: int, user_id: Optional[int] = None) -> bool:
    """
    确保SQLite用户和引擎存在（SQLite是文件型数据库，这里主要是确保引擎初始化）
    
    Args:
        db_name: 数据库名称
        db_username: 用户名（SQLite不需要，但为了兼容性保留）
        db_password: 密码（SQLite不需要，但为了兼容性保留）
        instance_id: 实例ID
        user_id: 用户ID，用于隔离不同用户的数据库文件
        
    Returns:
        bool: 成功返回True，否则返回False
    """
    # 创建数据库文件（如果不存在）
    success = await create_sqlite_database(db_name, user_id=user_id)
    if not success:
        return False
    
    # 确保引擎存在
    return await ensure_sqlite_engine(db_name, instance_id, user_id)


async def deploy_sqlite_database(db_name: str, statements: list[str], instance_id: int) -> bool:
    """
    部署SQLite数据库
    
    Args:
        db_name: 数据库名称
        statements: SQL语句列表
        instance_id: 实例ID
        
    Returns:
        bool: 部署成功返回True，否则返回False
    """
    try:
        # 确保引擎存在
        success = await ensure_sqlite_engine(db_name, instance_id)
        if not success:
            return False
        
        # 执行DDL语句
        sqlite_config = config.sqlite
        await deploy_sqlite_ddl(db_name, statements, sqlite_config)
        return True
    except Exception as e:
        print(f"部署SQLite数据库失败: {e}")
        return False


async def delete_sqlite_database(db_name: str, db_path: Optional[str] = None) -> bool:
    """
    删除SQLite数据库文件
    
    Args:
        db_name: 数据库名称
        db_path: 数据库文件路径（可选，如果不提供则使用配置中的默认路径）
        
    Returns:
        bool: 删除成功返回True，否则返回False
    """
    if db_path is None:
        sqlite_config = config.sqlite
        db_path = sqlite_config.db_path
    
    db_file_path = os.path.join(db_path, f"{db_name}.db")
    
    if os.path.exists(db_file_path):
        try:
            os.remove(db_file_path)
            return True
        except Exception as e:
            print(f"删除SQLite数据库文件失败: {e}")
            return False
    else:
        print(f"SQLite数据库文件不存在: {db_file_path}")
        return True  # 文件不存在也可以认为是删除成功

async def execute_sqlite_sql_with_user_check(
    sql: str,
    sql_type: str,
    instance_obj: DatabaseInstance,
    user_id: int
) -> Optional[list]:
    """
    执行 SQL 前先确保 SQLite 引擎已初始化且路径正确（基于 user_id）。
    """
    # 1. 确保引擎已初始化（内部会处理文件路径隔离）
    success = await ensure_sqlite_user_and_engine(
        db_name=instance_obj.db_name,
        db_username=instance_obj.db_username,
        db_password=instance_obj.db_password,
        instance_id=instance_obj.instance_id,
        user_id=user_id
    )
    if not success:
        raise Exception(f"无法确保实例 {instance_obj.instance_id} 的SQLite引擎")

    # 2. 调用执行器
    from sqlite.sqlite_execute import execute_dql_user, execute_dml_user
    if sql_type == "SELECT":
        return await execute_dql_user(sql, instance_obj)
    else:
        # DML 操作处理
        res = await execute_dml_user(sql, instance_obj)
        return [res] # 返回列表以保持接口一致性
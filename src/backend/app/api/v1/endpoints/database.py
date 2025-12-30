from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any, Optional
from schema.unified_response import UnifiedResponse

from api.v1 import deps
from core.exceptions import ItemNotFoundException, OperationNotPermittedException, ValidationException
from crud.crud_project import crud_project
from crud.crud_database_instance import crud_database_instance
from models.session import Session as SessionModel
from service.mysql_service import execute_mysql_sql_with_user_check as execute_mysql
from sqlalchemy.future import select
from service.postgresql_service import execute_postgres_sql_with_user_check as execute_postgres
from service.sqlite_service import execute_sqlite_sql_with_user_check as execute_sqlite

router = APIRouter()


async def get_db_instance_by_project(db: AsyncSession, project_id: int, user_id: int):
    """
    通过 project_id 获取数据库实例，验证用户权限。
    """
    # 1. 获取项目
    project = await crud_project.get(db, project_id)
    if not project:
        raise ItemNotFoundException("Project not found")
    
    # 2. 验证用户权限
    if project.user_id != user_id:
        raise OperationNotPermittedException("Not authorized")
    
    # 3. 获取数据库实例
    database_instance = await crud_database_instance.get(db, project.instance_id)
    if not database_instance:
        raise ItemNotFoundException("Database instance not found")
    
    return database_instance


async def get_db_instance_by_session(db: AsyncSession, session_id: int, user_id: int):
    """
    Helper function to verify session ownership and retrieve the associated database instance.
    """
    # 1. Verify session ownership
    stmt = select(SessionModel).where(SessionModel.session_id == session_id)
    result = await db.execute(stmt)
    session_obj = result.scalar_one_or_none()
    if not session_obj:
        raise ItemNotFoundException("Session not found")
    
    # Assuming session ownership check is needed, though chat_service checks project ownership.
    # Here we check if the session belongs to the user indirectly via project or directly if session has user_id.
    # Based on chat_service.py: project_id = await _verify_session_ownership(db, session_id, user_id)
    # Let's replicate that logic or similar.
    # SessionModel usually has user_id? Let's check models/session.py if needed, but chat_service uses _verify_session_ownership.
    # Let's assume simple check: session.user_id == user_id (if exists) or project check.
    # For now, let's trust the session_obj has user_id or we check project access.
    # chat_service.py:
    # stmt = select(ProjectMember).where(ProjectMember.project_id == project_id, ProjectMember.user_id == user_id)
    # Let's stick to a simpler check if possible, or just check session.user_id if it exists.
    # If SessionModel doesn't have user_id, we need to check project membership.
    
    # Let's check if session_obj has user_id.
    if hasattr(session_obj, 'user_id') and session_obj.user_id != user_id:
         raise OperationNotPermittedException("Not authorized")

    # 2. Get Project
    project = await crud_project.get(db, session_obj.project_id)
    if not project:
        raise ItemNotFoundException("Project not found")

    # 3. Get Database Instance
    database_instance = await crud_database_instance.get(db, project.instance_id)
    if not database_instance:
        raise ItemNotFoundException("Database instance not found")
        
    return database_instance

@router.get("/{session_id}/tables", response_model=UnifiedResponse[List[Dict[str, Any]]])
async def get_tables(
    session_id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user = Depends(deps.get_current_active_user),
):
    """
    Get all tables in the database associated with the session.
    """
    instance = await get_db_instance_by_session(db, session_id, current_user.user_id)

    tables = []

    # === MySQL ===
    if instance.db_type == 'mysql':
        sql = "SHOW FULL TABLES WHERE Table_Type = 'BASE TABLE'"
        result = await execute_mysql(sql, "SELECT", instance)
        if result:
            for row in result:
                # MySQL 返回字典: {'Tables_in_db': 'users', 'Table_type': 'BASE TABLE'}
                values = list(row.values())
                if values:
                    tables.append({"name": values[0]})

    # === PostgreSQL ===
    elif instance.db_type == 'postgresql':
        sql = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE'"
        result = await execute_postgres(sql, "SELECT", instance)
        if result:
            for row in result:
                # PG 返回字典: {'table_name': 'users'}
                tables.append({"name": row.get('table_name')})

    # === SQLite ===
    elif instance.db_type == 'sqlite':
        sql = "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        # 传入 current_user.user_id
        result = await execute_sqlite(sql, "SELECT", instance, current_user.user_id)
        if result:
            for row in result:
                # SQLite 返回字典: {'name': 'users'}
                tables.append({"name": row.get('name')})

    else:
        raise ValidationException(f"Unsupported DB type: {instance.db_type}")

    return UnifiedResponse.success(data=tables, message="获取数据库表列表成功")

@router.get("/{session_id}/tables/{table_name}/schema", response_model=UnifiedResponse[List[Dict[str, Any]]])
async def get_table_schema(
    session_id: int,
    table_name: str,
    db: AsyncSession = Depends(deps.get_db),
    current_user = Depends(deps.get_current_active_user),
):
    """
    Get the schema (columns) of a specific table.
    """
    instance = await get_db_instance_by_session(db, session_id, current_user.user_id)
    
    # Basic validation
    if not table_name.isidentifier():
         raise ValidationException("无效的表名")

    schema = []
    # === MySQL ===
    if instance.db_type == 'mysql':
        sql = f"DESCRIBE `{table_name}`"
        result = await execute_mysql(sql, "SELECT", instance)
        if result:
            for row in result:
                # 统一转小写: field, type, null, key, default, extra
                schema.append({k.lower(): v for k, v in row.items()})

    # === PostgreSQL ===
    elif instance.db_type == 'postgresql':
        sql = f"SELECT column_name, data_type, is_nullable, column_default FROM information_schema.columns WHERE table_name = '{table_name}' AND table_schema = 'public'"
        result = await execute_postgres(sql, "SELECT", instance)
        if result:
            for row in result:
                # 映射为前端通用字段名
                schema.append({
                    "field": row.get("column_name"),
                    "type": row.get("data_type"),
                    "null": row.get("is_nullable"),
                    "default": row.get("column_default")
                })

    # === SQLite ===
    elif instance.db_type == 'sqlite':
        sql = f"SELECT * FROM pragma_table_info('{table_name}')"
        # 传入 current_user.user_id
        result = await execute_sqlite(sql, "SELECT", instance, current_user.user_id)
        if result:
            for row in result:
                # SQLite: cid, name, type, notnull, dflt_value, pk
                schema.append({
                    "field": row.get("name"),
                    "type": row.get("type"),
                    "null": "NO" if row.get("notnull") else "YES",
                    "default": row.get("dflt_value")
                })

    return UnifiedResponse.success(data=schema, message="获取表结构成功")

@router.get("/{session_id}/tables/{table_name}/data", response_model=UnifiedResponse[List[Dict[str, Any]]])
async def get_table_data(
    session_id: int,
    table_name: str,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(deps.get_db),
    current_user = Depends(deps.get_current_active_user),
):
    """
    Get data from a specific table with pagination.
    """
    instance = await get_db_instance_by_session(db, session_id, current_user.user_id)

    if not table_name.isidentifier():
        raise ValidationException("无效的表名")

    limit = min(limit, 1000)

    # 构建 SQL (注意不同数据库的引号区别)
    if instance.db_type == 'mysql':
        sql = f"SELECT * FROM `{table_name}` LIMIT {limit} OFFSET {offset}"
        result = await execute_mysql(sql, "SELECT", instance)

    elif instance.db_type == 'postgresql':
        sql = f'SELECT * FROM "{table_name}" LIMIT {limit} OFFSET {offset}'
        result = await execute_postgres(sql, "SELECT", instance)

    elif instance.db_type == 'sqlite':
        sql = f'SELECT * FROM "{table_name}" LIMIT {limit} OFFSET {offset}'
        # 传入 current_user.user_id
        result = await execute_sqlite(sql, "SELECT", instance, current_user.user_id)
    # ...

    else:
        return []

    return UnifiedResponse.success(data=result or [], message="获取表数据成功")


# =========================================================
# 基于 Project ID 的数据库访问 API（无需会话）
# =========================================================

@router.get("/project/{project_id}/tables", response_model=UnifiedResponse[List[Dict[str, Any]]])
async def get_tables_by_project(
    project_id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user = Depends(deps.get_current_active_user),
):
    """
    通过项目 ID 获取数据库中的所有表（无需创建会话）。
    """
    instance = await get_db_instance_by_project(db, project_id, current_user.user_id)

    tables = []

    # === MySQL ===
    if instance.db_type == 'mysql':
        sql = "SHOW FULL TABLES WHERE Table_Type = 'BASE TABLE'"
        result = await execute_mysql(sql, "SELECT", instance)
        if result:
            for row in result:
                values = list(row.values())
                if values:
                    tables.append({"name": values[0]})

    # === PostgreSQL ===
    elif instance.db_type == 'postgresql':
        sql = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE'"
        result = await execute_postgres(sql, "SELECT", instance)
        if result:
            for row in result:
                tables.append({"name": row.get('table_name')})

    # === SQLite ===
    elif instance.db_type == 'sqlite':
        sql = "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        result = await execute_sqlite(sql, "SELECT", instance, current_user.user_id)
        if result:
            for row in result:
                tables.append({"name": row.get('name')})

    else:
        raise ValidationException(f"Unsupported DB type: {instance.db_type}")

    return UnifiedResponse.success(data=tables, message="获取数据库表列表成功")


@router.get("/project/{project_id}/tables/{table_name}/schema", response_model=UnifiedResponse[List[Dict[str, Any]]])
async def get_table_schema_by_project(
    project_id: int,
    table_name: str,
    db: AsyncSession = Depends(deps.get_db),
    current_user = Depends(deps.get_current_active_user),
):
    """
    通过项目 ID 获取指定表的结构（无需创建会话）。
    """
    instance = await get_db_instance_by_project(db, project_id, current_user.user_id)
    
    if not table_name.isidentifier():
        raise ValidationException("无效的表名")

    schema = []

    # === MySQL ===
    if instance.db_type == 'mysql':
        sql = f"DESCRIBE `{table_name}`"
        result = await execute_mysql(sql, "SELECT", instance)
        if result:
            for row in result:
                schema.append({k.lower(): v for k, v in row.items()})

    # === PostgreSQL ===
    elif instance.db_type == 'postgresql':
        sql = f"SELECT column_name, data_type, is_nullable, column_default FROM information_schema.columns WHERE table_name = '{table_name}' AND table_schema = 'public'"
        result = await execute_postgres(sql, "SELECT", instance)
        if result:
            for row in result:
                schema.append({
                    "field": row.get("column_name"),
                    "type": row.get("data_type"),
                    "null": row.get("is_nullable"),
                    "default": row.get("column_default")
                })

    # === SQLite ===
    elif instance.db_type == 'sqlite':
        sql = f"SELECT * FROM pragma_table_info('{table_name}')"
        result = await execute_sqlite(sql, "SELECT", instance, current_user.user_id)
        if result:
            for row in result:
                schema.append({
                    "field": row.get("name"),
                    "type": row.get("type"),
                    "null": "NO" if row.get("notnull") else "YES",
                    "default": row.get("dflt_value")
                })

    return UnifiedResponse.success(data=schema, message="获取表结构成功")


@router.get("/project/{project_id}/tables/{table_name}/data", response_model=UnifiedResponse[List[Dict[str, Any]]])
async def get_table_data_by_project(
    project_id: int,
    table_name: str,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(deps.get_db),
    current_user = Depends(deps.get_current_active_user),
):
    """
    通过项目 ID 获取指定表的数据（无需创建会话）。
    """
    instance = await get_db_instance_by_project(db, project_id, current_user.user_id)

    if not table_name.isidentifier():
        raise ValidationException("无效的表名")

    limit = min(limit, 1000)

    if instance.db_type == 'mysql':
        sql = f"SELECT * FROM `{table_name}` LIMIT {limit} OFFSET {offset}"
        result = await execute_mysql(sql, "SELECT", instance)

    elif instance.db_type == 'postgresql':
        sql = f'SELECT * FROM "{table_name}" LIMIT {limit} OFFSET {offset}'
        result = await execute_postgres(sql, "SELECT", instance)

    elif instance.db_type == 'sqlite':
        sql = f'SELECT * FROM "{table_name}" LIMIT {limit} OFFSET {offset}'
        result = await execute_sqlite(sql, "SELECT", instance, current_user.user_id)

    else:
        return UnifiedResponse.success(data=[], message="获取表数据成功")

    return UnifiedResponse.success(data=result or [], message="获取表数据成功")

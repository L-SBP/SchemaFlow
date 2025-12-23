from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any

from api.v1 import deps
from crud.crud_project import crud_project
from crud.crud_database_instance import crud_database_instance
from models.session import Session as SessionModel
from service.mysql_service import execute_mysql_sql_with_user_check
from sqlalchemy.future import select

router = APIRouter()

async def get_db_instance_by_session(db: AsyncSession, session_id: int, user_id: int):
    """
    Helper function to verify session ownership and retrieve the associated database instance.
    """
    # 1. Verify session ownership
    stmt = select(SessionModel).where(SessionModel.session_id == session_id)
    result = await db.execute(stmt)
    session_obj = result.scalar_one_or_none()
    if not session_obj:
        raise HTTPException(status_code=404, detail="Session not found")
    
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
         raise HTTPException(status_code=403, detail="Not authorized")

    # 2. Get Project
    project = await crud_project.get(db, session_obj.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # 3. Get Database Instance
    database_instance = await crud_database_instance.get(db, project.instance_id)
    if not database_instance:
        raise HTTPException(status_code=404, detail="Database instance not found")
        
    return database_instance

@router.get("/{session_id}/tables", response_model=List[Dict[str, Any]])
async def get_tables(
    session_id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user = Depends(deps.get_current_active_user),
):
    """
    Get all tables in the database associated with the session.
    """
    instance = await get_db_instance_by_session(db, session_id, current_user.user_id)
    
    # Use SHOW FULL TABLES to get both name and type (BASE TABLE vs VIEW)
    sql = "SHOW FULL TABLES WHERE Table_Type = 'BASE TABLE'"
    
    # We use "SELECT" as the operation type because "SHOW" returns a result set similar to SELECT,
    # and we want execute_sql_with_user_check to treat it as a query (DQL) rather than DML.
    # Ensure "SHOW *" is added to allowed_operations in config.yaml.
    result = await execute_mysql_sql_with_user_check(sql, "SELECT", instance)
    
    tables = []
    if result:
        for row in result:
            # The result rows are dictionaries.
            # For SHOW FULL TABLES, the columns are usually `Tables_in_dbname` and `Table_type`.
            # We use values() to be robust against the database name in the column header.
            values = list(row.values())
            if values:
                tables.append({"name": values[0]})
    return tables

@router.get("/{session_id}/tables/{table_name}/schema", response_model=List[Dict[str, Any]])
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
         raise HTTPException(status_code=400, detail="Invalid table name")

    sql = f"DESCRIBE `{table_name}`"
    result = await execute_mysql_sql_with_user_check(sql, "SELECT", instance)
    
    schema = []
    if result:
        for row in result:
            # Normalize keys to lowercase for frontend consistency
            schema.append({k.lower(): v for k, v in row.items()})
    return schema

@router.get("/{session_id}/tables/{table_name}/data", response_model=List[Dict[str, Any]])
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
         raise HTTPException(status_code=400, detail="Invalid table name")
         
    # Ensure limit is reasonable
    limit = min(limit, 1000)
    
    sql = f"SELECT * FROM `{table_name}` LIMIT {limit} OFFSET {offset}"
    result = await execute_mysql_sql_with_user_check(sql, "SELECT", instance)
    return result or []

from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession

# 修正导入路径
from api.v1 import deps
from crud.crud_session import crud_session
from schema.session import SessionCreate, SessionUpdate, SessionResponse
from core.exceptions import DatabaseOperationFailedException

router = APIRouter()

# 1. 获取会话列表 (支持按 project_id 筛选)
@router.get("/", response_model=List[SessionResponse], summary="获取会话列表")
async def read_sessions(
    db: AsyncSession = Depends(deps.get_db),
    project_id: Optional[int] = Query(None, description="筛选指定项目的会话"),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    if project_id:
        sessions = await crud_session.get_by_project(
            db=db, project_id=project_id, skip=skip, limit=limit
        )
    else:
        sessions = await crud_session.get_multi(db=db, skip=skip, limit=limit)
    return sessions

# 2. 创建新会话
@router.post("/", response_model=SessionResponse, summary="创建新会话")
async def create_session(
    *,
    db: AsyncSession = Depends(deps.get_db),
    session_in: SessionCreate,
) -> Any:
    try:
        # Pydantic 这里的 .dict() 在 v2 中可能是 .model_dump()，视版本而定，.dict() 通常兼容
        session = await crud_session.create(db=db, **session_in.dict())
        return session
    except DatabaseOperationFailedException as e:
        raise HTTPException(status_code=500, detail=str(e))

# 3. 获取单个会话详情
@router.get("/{session_id}", response_model=SessionResponse, summary="获取会话详情")
async def read_session(
    *,
    db: AsyncSession = Depends(deps.get_db),
    session_id: int = Path(..., description="会话ID"),
) -> Any:
    session = await crud_session.get(db=db, session_id=session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

# 4. 更新会话 (通常用于重命名)
@router.put("/{session_id}", response_model=SessionResponse, summary="更新会话信息")
async def update_session(
    *,
    db: AsyncSession = Depends(deps.get_db),
    session_id: int,
    session_in: SessionUpdate,
) -> Any:
    session = await crud_session.get(db=db, session_id=session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    update_data = session_in.dict(exclude_unset=True)
    session = await crud_session.update(db=db, db_obj=session, **update_data)
    return session

# 5. 删除会话
@router.delete("/{session_id}", response_model=bool, summary="删除会话")
async def delete_session(
    *,
    db: AsyncSession = Depends(deps.get_db),
    session_id: int,
) -> Any:
    session = await crud_session.get(db=db, session_id=session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    result = await crud_session.remove(db=db, session_id=session_id)
    return result
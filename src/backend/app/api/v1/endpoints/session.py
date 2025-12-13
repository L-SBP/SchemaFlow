from typing import List, Optional

from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1 import deps
from service.session_service import session_service
from schema.session import SessionCreate, SessionUpdate, SessionResponse
from schema.user import UserMe

router = APIRouter()


@router.get("/", response_model=List[SessionResponse], summary="获取会话列表")
async def read_sessions(
    db: AsyncSession = Depends(deps.get_db),
    current_user: UserMe = Depends(deps.get_current_active_user),
    project_id: Optional[int] = Query(None, description="筛选指定项目的会话"),
    skip: int = 0,
    limit: int = 100,
):
    """
    获取当前用户的会话列表，支持按项目筛选。
    """
    return await session_service.get_sessions(
        db=db,
        user=current_user,
        project_id=project_id,
        skip=skip,
        limit=limit
    )


@router.post("/", response_model=SessionResponse, summary="创建新会话")
async def create_session(
    db: AsyncSession = Depends(deps.get_db),
    current_user: UserMe = Depends(deps.get_current_active_user),
    session_in: SessionCreate = Depends(),
):
    """
    在指定项目下创建新的会话。
    """
    return await session_service.create_session(
        db=db,
        user=current_user,
        session_in=session_in
    )


@router.get("/{session_id}", response_model=SessionResponse, summary="获取会话详情")
async def read_session(
    db: AsyncSession = Depends(deps.get_db),
    current_user: UserMe = Depends(deps.get_current_active_user),
    session_id: int = Path(..., description="会话ID"),
):
    """
    获取单个会话详情，仅允许访问自身项目下的会话。
    """
    return await session_service.get_session(
        db=db,
        user=current_user,
        session_id=session_id
    )


@router.put("/{session_id}", response_model=SessionResponse, summary="更新会话信息")
async def update_session(
    db: AsyncSession = Depends(deps.get_db),
    current_user: UserMe = Depends(deps.get_current_active_user),
    session_id: int = Path(..., description="会话ID"),
    session_in: SessionUpdate = Depends(),
):
    """
    更新会话信息（如重命名）。
    """
    return await session_service.update_session(
        db=db,
        user=current_user,
        session_id=session_id,
        session_in=session_in
    )


@router.delete("/{session_id}", response_model=bool, summary="删除会话")
async def delete_session(
    db: AsyncSession = Depends(deps.get_db),
    current_user: UserMe = Depends(deps.get_current_active_user),
    session_id: int = Path(..., description="会话ID"),
):
    """
    删除会话，仅允许删除自身项目下的会话。
    """
    return await session_service.delete_session(
        db=db,
        user=current_user,
        session_id=session_id
    )

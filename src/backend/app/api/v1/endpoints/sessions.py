from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from src.backend.app.core.database import get_db
from src.backend.app.ai.chat.schemas import SessionCreate, SessionResponse
from src.backend.app.models.session import Session

router = APIRouter()

@router.post("/sessions", response_model=SessionResponse)
async def create_session(
    session_data: SessionCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    创建新会话
    
    - **project_id**: 关联的项目ID
    - **session_name**: 会话名称（可选，默认为"New Session"）
    """
    try:
        new_session = Session(
            project_id=session_data.project_id,
            session_name=session_data.session_name
        )
        
        db.add(new_session)
        await db.commit()
        await db.refresh(new_session)
        
        return SessionResponse(
            session_id=new_session.session_id,
            session_name=new_session.session_name,
            created_at=new_session.created_at,
            last_activity=new_session.last_activity
        )
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"创建会话失败: {str(e)}"
        )

@router.get("/projects/{project_id}/sessions", response_model=List[SessionResponse])
async def get_project_sessions(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    获取指定项目的所有会话
    """
    from sqlalchemy import select
    
    try:
        stmt = select(Session).where(
            Session.project_id == project_id
        ).order_by(Session.last_activity.desc())
        
        result = await db.execute(stmt)
        sessions = result.scalars().all()
        
        return [
            SessionResponse(
                session_id=session.session_id,
                session_name=session.session_name,
                created_at=session.created_at,
                last_activity=session.last_activity
            )
            for session in sessions
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取项目会话失败: {str(e)}"
        )

@router.get("/sessions/{session_id}")
async def get_session_detail(
    session_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    获取会话详情
    """
    from sqlalchemy import select
    
    try:
        stmt = select(Session).where(Session.session_id == session_id)
        result = await db.execute(stmt)
        session = result.scalar_one_or_none()
        
        if not session:
            raise HTTPException(status_code=404, detail="会话不存在")
        
        return SessionResponse(
            session_id=session.session_id,
            session_name=session.session_name,
            created_at=session.created_at,
            last_activity=session.last_activity
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取会话详情失败: {str(e)}"
        )
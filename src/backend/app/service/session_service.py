from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from crud.crud_session import crud_session
from crud.crud_project import crud_project
from schema.session import SessionCreate, SessionUpdate, SessionResponse
from schema.user import UserMe


class SessionService:
    """
    会话业务服务层：
    - 统一处理 Session 的业务逻辑
    - 统一处理鉴权与越权校验
    - endpoint 不应直接操作 crud
    """

    @staticmethod

    
    async def _check_project_owner(
        db: AsyncSession,
        project_id: int,
        user: UserMe
    ) -> None:
        """
        校验项目是否属于当前用户。
        这是 Session 鉴权的核心逻辑，所有涉及 project_id 的操作必须经过此校验。
        """
        project = await crud_project.get(db=db, project_id=project_id)
        if not project or project.user_id != user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Project access forbidden"
            )

    @staticmethod
    async def _check_session_owner(
        db: AsyncSession,
        session_id: int,
        user: UserMe
    ):
        """
        校验会话是否属于当前用户。
        通过 session → project → user 的链路进行校验，防止越权访问。
        """
        session = await crud_session.get(db=db, session_id=session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )

        await SessionService._check_project_owner(
            db=db,
            project_id=session.project_id,
            user=user
        )
        return session

    @staticmethod
    async def get_sessions(
        db: AsyncSession,
        user: UserMe,
        project_id: Optional[int],
        skip: int,
        limit: int
    ) -> List[SessionResponse]:
        """
        获取会话列表：
        - 支持按 project_id 过滤
        - 强制校验 project 属于当前用户
        """
        if project_id:
            await SessionService._check_project_owner(db, project_id, user)
            return await crud_session.get_by_project(
                db=db,
                project_id=project_id,
                skip=skip,
                limit=limit
            )

        # 如果不传 project_id，则返回当前用户所有项目下的会话
        return await crud_session.get_by_user(
            db=db,
            user_id=user.user_id,
            skip=skip,
            limit=limit
        )

    @staticmethod
    async def create_session(
        db: AsyncSession,
        user: UserMe,
        session_in: SessionCreate
    ) -> SessionResponse:
        """
        创建新会话：
        - 校验 project 属于当前用户
        - 统一由后端控制可写字段
        """
        await SessionService._check_project_owner(
            db=db,
            project_id=session_in.project_id,
            user=user
        )

        return await crud_session.create(
            db=db,
            **session_in.dict()
        )

    @staticmethod
    async def get_session(
        db: AsyncSession,
        user: UserMe,
        session_id: int
    ) -> SessionResponse:
        """
        获取单个会话详情。
        """
        return await SessionService._check_session_owner(
            db=db,
            session_id=session_id,
            user=user
        )

    @staticmethod
    async def update_session(
        db: AsyncSession,
        user: UserMe,
        session_id: int,
        session_in: SessionUpdate
    ) -> SessionResponse:
        """
        更新会话信息（如重命名）。
        """
        session = await SessionService._check_session_owner(
            db=db,
            session_id=session_id,
            user=user
        )

        update_data = session_in.dict(exclude_unset=True)
        return await crud_session.update(
            db=db,
            db_obj=session,
            **update_data
        )

    @staticmethod
    async def delete_session(
        db: AsyncSession,
        user: UserMe,
        session_id: int
    ) -> bool:
        """
        删除会话。
        """
        await SessionService._check_session_owner(
            db=db,
            session_id=session_id,
            user=user
        )
        return await crud_session.remove(
            db=db,
            session_id=session_id
        )


# 对外暴露的单例（保持与其他 service 风格一致）
session_service = SessionService()

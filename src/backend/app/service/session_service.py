"""
会话服务。

统一处理 Session 的业务逻辑，包括鉴权、越权校验及增删改查操作。
"""

# backend/app/service/session_service.py

from typing import List, Optional

from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from crud.crud_session import crud_session
from crud.crud_project import crud_project
from schema.session import SessionCreate, SessionUpdate, SessionResponse
from schema.user import UserMe
from core.log import log
from core.exceptions import ForbiddenException, ItemNotFoundException


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

        Args:
            db (AsyncSession): 数据库会话。
            project_id (int): 项目 ID。
            user (UserMe): 当前用户对象。

        Raises:
            ForbiddenException: 权限不足时抛出 403。
        """
        log.info("检查项目")
        project = await crud_project.get(db=db, project_id=project_id)
        log.info("检查项目2")
        if not project or project.user_id != user.user_id:
            log.info("检查项目3")
            raise ForbiddenException(message="Project access forbidden")

    @staticmethod
    async def _check_session_owner(
        db: AsyncSession,
        session_id: int,
        user: UserMe
    ):
        """
        校验会话是否属于当前用户。
        
        通过 session → project → user 的链路进行校验，防止越权访问。

        Args:
            db (AsyncSession): 数据库会话。
            session_id (int): 会话 ID。
            user (UserMe): 当前用户对象。

        Returns:
            Session: 会话对象。

        Raises:
            ItemNotFoundException: 会话不存在或权限不足时抛出。
        """
        session = await crud_session.get(db=db, session_id=session_id)
        if not session:
            raise ItemNotFoundException(message="Session not found")

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
        获取会话列表。

        支持按 project_id 过滤，强制校验 project 属于当前用户。

        Args:
            db (AsyncSession): 数据库会话。
            user (UserMe): 当前用户对象。
            project_id (Optional[int]): 项目 ID 过滤。
            skip (int): 跳过数量。
            limit (int): 返回限制。

        Returns:
            List[SessionResponse]: 会话列表。
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
    async def get_sessions_count(
        db: AsyncSession,
        user: UserMe,
        project_id: Optional[int]
    ) -> int:
        """
        获取会话总数。

        支持按 project_id 过滤，强制校验 project 属于当前用户。

        Args:
            db (AsyncSession): 数据库会话。
            user (UserMe): 当前用户对象。
            project_id (Optional[int]): 项目 ID 过滤。

        Returns:
            int: 会话总数。
        """
        if project_id:
            await SessionService._check_project_owner(db, project_id, user)
            return await crud_session.count_by_project(
                db=db,
                project_id=project_id
            )

        # 如果不传 project_id，则返回当前用户所有项目下的会话总数
        return await crud_session.count_by_user(
            db=db,
            user_id=user.user_id
        )

    @staticmethod
    async def create_session(
        db: AsyncSession,
        user: UserMe,
        session_in: SessionCreate
    ) -> SessionResponse:
        """
        创建新会话。
        
        - 校验 project 属于当前用户
        - 统一由后端控制可写字段

        Args:
            db (AsyncSession): 数据库会话。
            user (UserMe): 当前用户对象。
            session_in (SessionCreate): 会话创建参数。

        Returns:
            SessionResponse: 创建后的会话。
        """
        log.info("创建会话2")
        await SessionService._check_project_owner(
            db=db,
            project_id=session_in.project_id,
            user=user
        )
        log.info("创建会话3")
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

        Args:
            db (AsyncSession): 数据库会话。
            user (UserMe): 当前用户对象。
            session_id (int): 会话 ID。

        Returns:
            SessionResponse: 会话详情。
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

        Args:
            db (AsyncSession): 数据库会话。
            user (UserMe): 当前用户对象。
            session_id (int): 会话 ID。
            session_in (SessionUpdate): 会话更新参数。

        Returns:
            SessionResponse: 更新后的会话。
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

        Args:
            db (AsyncSession): 数据库会话。
            user (UserMe): 当前用户对象。
            session_id (int): 会话 ID。

        Returns:
            bool: 是否删除成功。
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

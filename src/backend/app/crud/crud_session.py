"""
会话 CRUD。

本模块提供聊天会话的 CRUD 操作。
"""

# backend/app/crud/crud_session.py

from typing import Optional, List
from sqlalchemy.future import select
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from models.session import Session
from core.exceptions import DatabaseOperationFailedException


class CRUDSession:
    @staticmethod
    async def create(db: AsyncSession, **kwargs) -> Session:
        """
        创建新的会话。

        Args:
            db (AsyncSession): 数据库会话。
            **kwargs: 会话字段。

        Returns:
            Session: 创建的会话对象。

        Raises:
            DatabaseOperationFailedException: 创建失败时抛出。
        """
        try:
            db_obj = Session(**kwargs)
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)
            return db_obj
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseOperationFailedException("create session") from e

    @staticmethod
    async def get(db: AsyncSession, session_id: int) -> Optional[Session]:
        """
        根据会话ID获取会话。

        Args:
            db (AsyncSession): 数据库会话。
            session_id (int): 会话ID。

        Returns:
            Optional[Session]: 如果找到返回会话对象，否则返回None。

        Raises:
            DatabaseOperationFailedException: 查询失败时抛出。
        """
        try:
            query = select(Session).where(Session.session_id == session_id)
            result = await db.execute(query)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            raise DatabaseOperationFailedException("get session") from e

    @staticmethod
    async def get_by_project(db: AsyncSession, project_id: int, skip: int = 0, limit: int = 100) -> List[Session]:
        """
        根据项目ID获取会话列表。

        Args:
            db (AsyncSession): 数据库会话。
            project_id (int): 项目ID。
            skip (int): 跳过的记录数。
            limit (int): 最大返回记录数。

        Returns:
            List[Session]: 会话对象列表。

        Raises:
            DatabaseOperationFailedException: 查询失败时抛出。
        """
        try:
            query = select(Session).where(Session.project_id == project_id).offset(skip).limit(limit)
            result = await db.execute(query)
            return result.scalars().all()
        except SQLAlchemyError as e:
            raise DatabaseOperationFailedException("get sessions by project") from e

    @staticmethod
    async def get_multi(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Session]:
        """
        分页获取多个会话。

        Args:
            db (AsyncSession): 数据库会话。
            skip (int): 跳过的记录数。
            limit (int): 最大返回记录数。

        Returns:
            List[Session]: 会话对象列表。

        Raises:
            DatabaseOperationFailedException: 查询失败时抛出。
        """
        try:
            query = select(Session).offset(skip).limit(limit)
            result = await db.execute(query)
            return result.scalars().all()
        except SQLAlchemyError as e:
            raise DatabaseOperationFailedException("get multiple sessions") from e

    @staticmethod
    async def update(db: AsyncSession, db_obj: Session, **kwargs) -> Session:
        """
        更新会话。

        Args:
            db (AsyncSession): 数据库会话。
            db_obj (Session): 要更新的会话对象。
            **kwargs: 要更新的字段。

        Returns:
            Session: 更新后的会话对象。

        Raises:
            DatabaseOperationFailedException: 更新失败时抛出。
        """
        try:
            for field, value in kwargs.items():
                setattr(db_obj, field, value)
            await db.commit()
            await db.refresh(db_obj)
            return db_obj
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseOperationFailedException("update session") from e

    @staticmethod
    async def remove(db: AsyncSession, session_id: int) -> bool:
        """
        根据会话ID删除会话。

        Args:
            db (AsyncSession): 数据库会话。
            session_id (int): 会话ID。

        Returns:
            bool: 如果会话被删除返回True，如果未找到会话返回False。

        Raises:
            DatabaseOperationFailedException: 删除失败时抛出。
        """
        try:
            query = delete(Session).where(Session.session_id == session_id)
            result = await db.execute(query)
            await db.commit()
            return result.rowcount > 0
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseOperationFailedException("delete session") from e

    @staticmethod
    async def update_last_activity(db: AsyncSession, session_id: int) -> Optional[Session]:
        """
        更新会话的最后活动时间。

        Args:
            db (AsyncSession): 数据库会话。
            session_id (int): 会话ID。

        Returns:
            Optional[Session]: 更新后的会话对象，如果未找到会话返回None。

        Raises:
            DatabaseOperationFailedException: 更新失败时抛出。
        """
        try:
            session = await CRUDSession.get(db, session_id)
            if session:
           
                await db.commit()
                await db.refresh(session)
            return session
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseOperationFailedException("update session last activity") from e

crud_session = CRUDSession()
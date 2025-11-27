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
        创建新的会话
        
        :param db: 数据库会话
        :param kwargs: 会话字段
        :return: 创建的会话对象
        :raises SQLAlchemyError: 如果发生数据库错误
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
        根据会话ID获取会话
        
        :param db: 数据库会话
        :param session_id: 会话ID
        :return: 如果找到返回会话对象，否则返回None
        :raises DatabaseOperationFailedException: 如果发生数据库错误
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
        根据项目ID获取会话列表
        
        :param db: 数据库会话
        :param project_id: 项目ID
        :param skip: 跳过的记录数
        :param limit: 最大返回记录数
        :return: 会话对象列表
        :raises DatabaseOperationFailedException: 如果发生数据库错误
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
        分页获取多个会话
        
        :param db: 数据库会话
        :param skip: 跳过的记录数
        :param limit: 最大返回记录数
        :return: 会话对象列表
        :raises DatabaseOperationFailedException: 如果发生数据库错误
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
        更新会话
        
        :param db: 数据库会话
        :param db_obj: 要更新的会话对象
        :param kwargs: 要更新的字段
        :return: 更新后的会话对象
        :raises SQLAlchemyError: 如果发生数据库错误
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
        根据会话ID删除会话
        
        :param db: 数据库会话
        :param session_id: 会话ID
        :return: 如果会话被删除返回True，如果未找到会话返回False
        :raises SQLAlchemyError: 如果发生数据库错误
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
        更新会话的最后活动时间
        
        :param db: 数据库会话
        :param session_id: 会话ID
        :return: 更新后的会话对象，如果未找到会话返回None
        :raises DatabaseOperationFailedException: 如果发生数据库错误
        """
        try:
            session = await CRUDSession.get(db, session_id)
            if session:
                # The last_activity field will be automatically updated on commit due to onupdate=func.now()
                await db.commit()
                await db.refresh(session)
            return session
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseOperationFailedException("update session last activity") from e

crud_session = CRUDSession()
from typing import Optional, List
from sqlalchemy.future import select
from sqlalchemy import update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql.operators import or_

from models.user_account import UserAccount
from core.exceptions import DatabaseOperationFailedException


class CRUDUserAccount:
    @staticmethod
    async def create(db: AsyncSession, **kwargs) -> UserAccount:
        """
        创建新的用户账户
        
        :param db: 数据库会话
        :param kwargs: 用户账户字段
        :return: 创建的用户账户对象
        :raises SQLAlchemyError: 如果发生数据库错误
        """
        try:
            db_obj = UserAccount(**kwargs)
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)
            return db_obj
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseOperationFailedException("create user") from e

    @staticmethod
    async def get(db: AsyncSession, user_id: int) -> Optional[UserAccount]:
        """
        根据用户ID获取用户账户
        
        :param db: 数据库会话
        :param user_id: 用户ID
        :return: 如果找到返回用户账户对象，否则返回None
        :raises DatabaseOperationFailedException: 如果发生数据库错误
        """
        try:
            query = select(UserAccount).where(UserAccount.user_id == user_id)
            result = await db.execute(query)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            raise DatabaseOperationFailedException("get user") from e

    @staticmethod
    async def get_by_username(db: AsyncSession, username: str) -> Optional[UserAccount]:
        """
        根据用户名获取用户账户
        
        :param db: 数据库会话
        :param username: 用户名
        :return: 如果找到返回用户账户对象，否则返回None
        :raises DatabaseOperationFailedException: 如果发生数据库错误
        """
        try:
            query = select(UserAccount).where(UserAccount.username == username)
            result = await db.execute(query)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            raise DatabaseOperationFailedException("get user by username") from e

    @staticmethod
    async def get_by_email(db: AsyncSession, email: str) -> Optional[UserAccount]:
        """
        根据邮箱获取用户账户
        
        :param db: 数据库会话
        :param email: 邮箱地址
        :return: 如果找到返回用户账户对象，否则返回None
        :raises DatabaseOperationFailedException: 如果发生数据库错误
        """
        try:
            query = select(UserAccount).where(UserAccount.email == email)
            result = await db.execute(query)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            raise DatabaseOperationFailedException("get user by email") from e

    @staticmethod
    async def get_multi(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[UserAccount]:
        """
        分页获取多个用户账户
        
        :param db: 数据库会话
        :param skip: 跳过的记录数
        :param limit: 最大返回记录数
        :return: 用户账户对象列表
        :raises DatabaseOperationFailedException: 如果发生数据库错误
        """
        try:
            query = select(UserAccount).offset(skip).limit(limit)
            result = await db.execute(query)
            return result.scalars().all()
        except SQLAlchemyError as e:
            raise DatabaseOperationFailedException("get multiple users") from e

    @staticmethod
    async def update(db: AsyncSession, db_obj: UserAccount, **kwargs) -> UserAccount:
        """
        更新用户账户
        
        :param db: 数据库会话
        :param db_obj: 要更新的用户账户对象
        :param kwargs: 要更新的字段
        :return: 更新后的用户账户对象
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
            raise DatabaseOperationFailedException("update user") from e

    @staticmethod
    async def remove(db: AsyncSession, user_id: int) -> bool:
        """
        根据用户ID删除用户账户
        
        :param db: 数据库会话
        :param user_id: 用户ID
        :return: 如果用户被删除返回True，如果未找到用户返回False
        :raises SQLAlchemyError: 如果发生数据库错误
        """
        try:
            query = delete(UserAccount).where(UserAccount.user_id == user_id)
            result = await db.execute(query)
            await db.commit()
            return result.rowcount > 0
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseOperationFailedException("delete user") from e

    @staticmethod
    async def get_by_username_or_email(db: AsyncSession, username_or_email: str) -> Optional[UserAccount]:
        """
        根据用户名或邮箱获取用户

        :param db: 数据库会话
        :param username_or_email: 用户名或邮箱
        :return: 如果找到返回用户账户对象，否则返回None
        :raises DatabaseOperationFailedException: 如果发生数据库错误
        """
        try:
            query = select(UserAccount).where(
                or_(
                    UserAccount.username == username_or_email,
                    UserAccount.email == username_or_email
                )
            )
            result = await db.execute(query)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            raise DatabaseOperationFailedException("get user by username or email") from e

crud_user_account = CRUDUserAccount()

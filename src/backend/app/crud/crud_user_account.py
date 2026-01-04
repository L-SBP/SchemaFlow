"""
用户账户 CRUD。

本模块提供用户账户管理的 CRUD 操作。
"""

# backend/app/crud/crud_user_account.py

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
        创建新的用户账户。

        Args:
            db (AsyncSession): 数据库会话。
            **kwargs: 用户账户字段。

        Returns:
            UserAccount: 创建的用户账户对象。

        Raises:
            DatabaseOperationFailedException: 创建失败时抛出。
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
        根据用户ID获取用户账户。

        Args:
            db (AsyncSession): 数据库会话。
            user_id (int): 用户ID。

        Returns:
            Optional[UserAccount]: 如果找到返回用户账户对象，否则返回None。

        Raises:
            DatabaseOperationFailedException: 查询失败时抛出。
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
        根据用户名获取用户账户。

        Args:
            db (AsyncSession): 数据库会话。
            username (str): 用户名。

        Returns:
            Optional[UserAccount]: 如果找到返回用户账户对象，否则返回None。

        Raises:
            DatabaseOperationFailedException: 查询失败时抛出。
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
        根据邮箱获取用户账户。

        Args:
            db (AsyncSession): 数据库会话。
            email (str): 邮箱地址。

        Returns:
            Optional[UserAccount]: 如果找到返回用户账户对象，否则返回None。

        Raises:
            DatabaseOperationFailedException: 查询失败时抛出。
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
        分页获取多个用户账户。

        Args:
            db (AsyncSession): 数据库会话。
            skip (int): 跳过的记录数。
            limit (int): 最大返回记录数。

        Returns:
            List[UserAccount]: 用户账户对象列表。

        Raises:
            DatabaseOperationFailedException: 查询失败时抛出。
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
        更新用户账户。

        Args:
            db (AsyncSession): 数据库会话。
            db_obj (UserAccount): 要更新的用户账户对象。
            **kwargs: 要更新的字段。

        Returns:
            UserAccount: 更新后的用户账户对象。

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
            raise DatabaseOperationFailedException("update user") from e

    @staticmethod
    async def remove(db: AsyncSession, user_id: int) -> bool:
        """
        根据用户ID删除用户账户。

        Args:
            db (AsyncSession): 数据库会话。
            user_id (int): 用户ID。

        Returns:
            bool: 如果用户被删除返回True，如果未找到用户返回False。

        Raises:
            DatabaseOperationFailedException: 删除失败时抛出。
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
        根据用户名或邮箱获取用户。

        Args:
            db (AsyncSession): 数据库会话。
            username_or_email (str): 用户名或邮箱。

        Returns:
            Optional[UserAccount]: 如果找到返回用户账户对象，否则返回None。

        Raises:
            DatabaseOperationFailedException: 查询失败时抛出。
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

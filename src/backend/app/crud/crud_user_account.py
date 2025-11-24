from typing import Optional, List
from sqlalchemy.future import select
from sqlalchemy import update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql.operators import or_

from models.user_account import UserAccount


class CRUDUserAccount:
    @staticmethod
    async def create(db: AsyncSession, **kwargs) -> UserAccount:
        """
        Create a new user account
        
        Args:
            db: Database session
            **kwargs: User account fields
            
        Returns:
            UserAccount: Created user account object
            
        Raises:
            SQLAlchemyError: If there's a database error
        """
        try:
            db_obj = UserAccount(**kwargs)
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)
            return db_obj
        except SQLAlchemyError:
            await db.rollback()
            raise

    @staticmethod
    async def get(db: AsyncSession, user_id: int) -> Optional[UserAccount]:
        """
        Get user account by user_id
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            Optional[UserAccount]: User account object if found, None otherwise
        """
        query = select(UserAccount).where(UserAccount.user_id == user_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_username(db: AsyncSession, username: str) -> Optional[UserAccount]:
        """
        Get user account by username
        
        Args:
            db: Database session
            username: Username
            
        Returns:
            Optional[UserAccount]: User account object if found, None otherwise
        """
        query = select(UserAccount).where(UserAccount.username == username)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_email(db: AsyncSession, email: str) -> Optional[UserAccount]:
        """
        Get user account by email
        
        Args:
            db: Database session
            email: Email address
            
        Returns:
            Optional[UserAccount]: User account object if found, None otherwise
        """
        query = select(UserAccount).where(UserAccount.email == email)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_multi(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[UserAccount]:
        """
        Get multiple user accounts with pagination
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[UserAccount]: List of user account objects
        """
        query = select(UserAccount).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def update(db: AsyncSession, db_obj: UserAccount, **kwargs) -> UserAccount:
        """
        Update user account
        
        Args:
            db: Database session
            db_obj: User account object to update
            **kwargs: Fields to update
            
        Returns:
            UserAccount: Updated user account object
            
        Raises:
            SQLAlchemyError: If there's a database error
        """
        try:
            for field, value in kwargs.items():
                setattr(db_obj, field, value)
            await db.commit()
            await db.refresh(db_obj)
            return db_obj
        except SQLAlchemyError:
            await db.rollback()
            raise

    @staticmethod
    async def remove(db: AsyncSession, user_id: int) -> bool:
        """
        Remove user account by user_id
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            bool: True if user was deleted, False if user was not found
            
        Raises:
            SQLAlchemyError: If there's a database error
        """
        try:
            query = delete(UserAccount).where(UserAccount.user_id == user_id)
            result = await db.execute(query)
            await db.commit()
            return result.rowcount > 0
        except SQLAlchemyError:
            await db.rollback()
            raise

    @staticmethod
    async def get_by_username_or_email(db: AsyncSession, username_or_email: str) -> Optional[UserAccount]:
        """
        Get user by username or email

        Args:
            db: Database session
            username_or_email: Username or email

        Returns:
            Optional[UserAccount]: User account if found, None otherwise
        """
        query = select(UserAccount).where(
            or_(
                UserAccount.username == username_or_email,
                UserAccount.email == username_or_email
            )
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

curd_user_account = CRUDUserAccount()
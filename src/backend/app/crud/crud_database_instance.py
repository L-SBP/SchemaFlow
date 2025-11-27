from typing import Optional, List
from sqlalchemy.future import select
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from models.database_instance import DatabaseInstance
from core.exceptions import DatabaseOperationFailedException


class CRUDDatabaseInstance:
    @staticmethod
    async def create(db: AsyncSession, **kwargs) -> DatabaseInstance:
        """
        创建新的数据库实例
        
        :param db: 数据库会话
        :param kwargs: 数据库实例字段
        :return: 创建的数据库实例对象
        :raises SQLAlchemyError: 如果发生数据库错误
        """
        try:
            db_obj = DatabaseInstance(**kwargs)
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)
            return db_obj
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseOperationFailedException("create database instance") from e

    @staticmethod
    async def get(db: AsyncSession, instance_id: int) -> Optional[DatabaseInstance]:
        """
        根据实例ID获取数据库实例
        
        :param db: 数据库会话
        :param instance_id: 实例ID
        :return: 如果找到返回数据库实例对象，否则返回None
        :raises DatabaseOperationFailedException: 如果发生数据库错误
        """
        try:
            query = select(DatabaseInstance).where(DatabaseInstance.instance_id == instance_id)
            result = await db.execute(query)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            raise DatabaseOperationFailedException("get database instance") from e

    @staticmethod
    async def get_by_status(db: AsyncSession, status: str, skip: int = 0, limit: int = 100) -> List[DatabaseInstance]:
        """
        根据状态获取数据库实例列表
        
        :param db: 数据库会话
        :param status: 实例状态
        :param skip: 跳过的记录数
        :param limit: 最大返回记录数
        :return: 数据库实例对象列表
        :raises DatabaseOperationFailedException: 如果发生数据库错误
        """
        try:
            query = select(DatabaseInstance).where(DatabaseInstance.status == status).offset(skip).limit(limit)
            result = await db.execute(query)
            return result.scalars().all()
        except SQLAlchemyError as e:
            raise DatabaseOperationFailedException("get database instances by status") from e

    @staticmethod
    async def get_multi(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[DatabaseInstance]:
        """
        分页获取多个数据库实例
        
        :param db: 数据库会话
        :param skip: 跳过的记录数
        :param limit: 最大返回记录数
        :return: 数据库实例对象列表
        :raises DatabaseOperationFailedException: 如果发生数据库错误
        """
        try:
            query = select(DatabaseInstance).offset(skip).limit(limit)
            result = await db.execute(query)
            return result.scalars().all()
        except SQLAlchemyError as e:
            raise DatabaseOperationFailedException("get multiple database instances") from e

    @staticmethod
    async def update(db: AsyncSession, db_obj: DatabaseInstance, **kwargs) -> DatabaseInstance:
        """
        更新数据库实例
        
        :param db: 数据库会话
        :param db_obj: 要更新的数据库实例对象
        :param kwargs: 要更新的字段
        :return: 更新后的数据库实例对象
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
            raise DatabaseOperationFailedException("update database instance") from e

    @staticmethod
    async def remove(db: AsyncSession, instance_id: int) -> bool:
        """
        根据实例ID删除数据库实例
        
        :param db: 数据库会话
        :param instance_id: 实例ID
        :return: 如果实例被删除返回True，如果未找到实例返回False
        :raises SQLAlchemyError: 如果发生数据库错误
        """
        try:
            query = delete(DatabaseInstance).where(DatabaseInstance.instance_id == instance_id)
            result = await db.execute(query)
            await db.commit()
            return result.rowcount > 0
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseOperationFailedException("delete database instance") from e

    @staticmethod
    async def change_status(db: AsyncSession, instance_id: int, status: str) -> Optional[DatabaseInstance]:
        """
        更改数据库实例状态
        
        :param db: 数据库会话
        :param instance_id: 实例ID
        :param status: 新的状态值
        :return: 更新后的数据库实例对象，如果未找到实例返回None
        :raises DatabaseOperationFailedException: 如果发生数据库错误
        """
        try:
            instance = await CRUDDatabaseInstance.get(db, instance_id)
            if instance:
                instance.status = status
                await db.commit()
                await db.refresh(instance)
            return instance
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseOperationFailedException("change database instance status") from e

crud_database_instance = CRUDDatabaseInstance()
from typing import Optional, List
from sqlalchemy.future import select
from sqlalchemy import update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from models.project import Project
from core.exceptions import DatabaseOperationFailedException


class CRUDProject:
    @staticmethod
    async def create(db: AsyncSession, **kwargs) -> Project:
        """
        创建新项目
        
        :param db: 数据库会话
        :param kwargs: 项目字段
        :return: 创建的项目对象
        :raises SQLAlchemyError: 如果发生数据库错误
        """
        try:
            db_obj = Project(**kwargs)
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)
            return db_obj
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseOperationFailedException("create project") from e

    @staticmethod
    async def get(db: AsyncSession, project_id: int) -> Optional[Project]:
        """
        根据项目ID获取项目
        
        :param db: 数据库会话
        :param project_id: 项目ID
        :return: 如果找到返回项目对象，否则返回None
        :raises DatabaseOperationFailedException: 如果发生数据库错误
        """
        try:
            query = select(Project).where(Project.project_id == project_id)
            result = await db.execute(query)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            raise DatabaseOperationFailedException("get project") from e

    @staticmethod
    async def get_by_user(db: AsyncSession, user_id: int, skip: int = 0, limit: int = 100) -> List[Project]:
        """
        根据用户ID获取项目列表
        
        :param db: 数据库会话
        :param user_id: 用户ID
        :param skip: 跳过的记录数
        :param limit: 最大返回记录数
        :return: 项目对象列表
        :raises DatabaseOperationFailedException: 如果发生数据库错误
        """
        try:
            query = select(Project).where(Project.user_id == user_id).offset(skip).limit(limit)
            result = await db.execute(query)
            return result.scalars().all()
        except SQLAlchemyError as e:
            raise DatabaseOperationFailedException("get projects by user") from e

    @staticmethod
    async def get_multi(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Project]:
        """
        分页获取多个项目
        
        :param db: 数据库会话
        :param skip: 跳过的记录数
        :param limit: 最大返回记录数
        :return: 项目对象列表
        :raises DatabaseOperationFailedException: 如果发生数据库错误
        """
        try:
            query = select(Project).offset(skip).limit(limit)
            result = await db.execute(query)
            return result.scalars().all()
        except SQLAlchemyError as e:
            raise DatabaseOperationFailedException("get multiple projects") from e

    @staticmethod
    async def update(db: AsyncSession, db_obj: Project, **kwargs) -> Project:
        """
        更新项目
        
        :param db: 数据库会话
        :param db_obj: 要更新的项目对象
        :param kwargs: 要更新的字段
        :return: 更新后的项目对象
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
            raise DatabaseOperationFailedException("update project") from e

    @staticmethod
    async def remove(db: AsyncSession, project_id: int) -> bool:
        """
        根据项目ID删除项目
        
        :param db: 数据库会话
        :param project_id: 项目ID
        :return: 如果项目被删除返回True，如果未找到项目返回False
        :raises SQLAlchemyError: 如果发生数据库错误
        """
        try:
            query = delete(Project).where(Project.project_id == project_id)
            result = await db.execute(query)
            await db.commit()
            return result.rowcount > 0
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseOperationFailedException("delete project") from e

    @staticmethod
    async def change_status(db: AsyncSession, project_id: int, status: str) -> Optional[Project]:
        """
        更改项目状态
        
        :param db: 数据库会话
        :param project_id: 项目ID
        :param status: 新的状态值
        :return: 更新后的项目对象，如果未找到项目返回None
        :raises DatabaseOperationFailedException: 如果发生数据库错误
        """
        try:
            project = await CRUDProject.get(db, project_id)
            if project:
                project.project_status = status
                await db.commit()
                await db.refresh(project)
            return project
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseOperationFailedException("change project status") from e

crud_project = CRUDProject()
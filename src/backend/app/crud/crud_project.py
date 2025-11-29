# backend/app/crud/crud_project.py

from typing import Optional, List
from sqlalchemy.future import select
from sqlalchemy import update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timezone

# 隐式绝对导入
from models.project import Project
from core.exceptions import DatabaseOperationFailedException


class CRUDProject:
    @staticmethod
    async def create(db: AsyncSession, **kwargs) -> Project:
        """创建新项目"""
        try:
            # 自动填充时间
            if 'created_at' not in kwargs:
                kwargs['created_at'] = datetime.now(timezone.utc)
            if 'updated_at' not in kwargs:
                kwargs['updated_at'] = datetime.now(timezone.utc)

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
        """获取单个项目"""
        try:
            query = select(Project).where(Project.project_id == project_id)
            result = await db.execute(query)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            raise DatabaseOperationFailedException("get project") from e

    @staticmethod
    async def get_by_user(
            db: AsyncSession, user_id: int, skip: int = 0, limit: int = 100, search: Optional[str] = None
    ) -> List[Project]:
        """获取用户项目列表 (支持分页、搜索、排除已删除)"""
        try:
            query = select(Project).where(
                Project.user_id == user_id,
                Project.project_status != 'deleted'  # 软删除过滤
            )
            if search:
                query = query.where(Project.project_name.ilike(f'%{search}%'))

            query = query.offset(skip).limit(limit).order_by(Project.updated_at.desc())
            result = await db.execute(query)
            return result.scalars().all()
        except SQLAlchemyError as e:
            raise DatabaseOperationFailedException("get projects list") from e

    @staticmethod
    async def get_total_count_by_user(
            db: AsyncSession, user_id: int, search: Optional[str] = None
    ) -> int:
        """获取总记录数 (用于分页)"""
        try:
            query = select(func.count(Project.project_id)).where(
                Project.user_id == user_id,
                Project.project_status != 'deleted'
            )
            if search:
                query = query.where(Project.project_name.ilike(f'%{search}%'))
            result = await db.execute(query)
            return result.scalar_one()
        except SQLAlchemyError as e:
            raise DatabaseOperationFailedException("get project count") from e

    @staticmethod
    async def update(db: AsyncSession, project_id: int, **kwargs) -> Optional[Project]:
        """更新项目"""
        try:
            kwargs['updated_at'] = datetime.now(timezone.utc)
            query = update(Project).where(Project.project_id == project_id).values(**kwargs).execution_options(
                synchronize_session="fetch")
            await db.execute(query)
            await db.commit()
            return await CRUDProject.get(db, project_id)
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseOperationFailedException("update project") from e

    @staticmethod
    async def change_status(db: AsyncSession, project_id: int, status: str) -> Optional[Project]:
        """更改状态 (用于软删除)"""
        return await CRUDProject.update(db, project_id, project_status=status)


crud_project = CRUDProject()
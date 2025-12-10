# backend/app/crud/crud_project.py

from typing import Optional, List
from sqlalchemy.future import select
from sqlalchemy import update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timezone

# 隐式绝对导入
from models.project import Project
from models.database_instance import DatabaseInstance  # <--- 1. 新增导入
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
            # 修改查询：同时查 Project 和 DatabaseInstance.db_type
            query = select(Project, DatabaseInstance.db_type) \
                .join(DatabaseInstance, Project.instance_id == DatabaseInstance.instance_id) \
                .where(Project.project_id == project_id)

            result = await db.execute(query)
            row = result.first()  # 获取第一行结果，形式为 (Project实例, db_type字符串)

            if row:
                project_obj, db_type_val = row
                # 动态将 db_type 属性挂载到 project_obj 上
                # 这样 Pydantic (from_attributes=True) 就能读取到 project_obj.db_type
                setattr(project_obj, "db_type", db_type_val)
                return project_obj

            return None
        except SQLAlchemyError as e:
            raise DatabaseOperationFailedException("get project") from e

    @staticmethod
    async def get_by_user(
            db: AsyncSession, user_id: int, skip: int = 0, limit: int = 100, search: Optional[str] = None
    ) -> List[Project]:
        """
        获取指定用户的项目列表，支持分页和模糊搜索。

        Args:
            db (AsyncSession): 数据库会话。
            user_id (int): 用户ID。
            skip (int, optional): 跳过的记录数。
            limit (int, optional): 返回的最大记录数。
            search (Optional[str], optional): 项目名称模糊搜索关键字。

        Returns:
            List[Project]: 项目对象列表。

        Raises:
            DatabaseOperationFailedException: 查询失败时抛出。
        """
        try:
            # 修改查询：Join DatabaseInstance
            query = select(Project, DatabaseInstance.db_type).join(
                DatabaseInstance, Project.instance_id == DatabaseInstance.instance_id
            ).where(
                Project.user_id == user_id,
                Project.project_status != 'deleted'
            )

            if search:
                query = query.where(Project.project_name.ilike(f'%{search}%'))

            query = query.offset(skip).limit(limit).order_by(Project.updated_at.desc())

            result = await db.execute(query)
            rows = result.all()  # 结果是 list of (Project, str)

            projects = []
            for p, dt in rows:
                # 动态赋值
                setattr(p, "db_type", dt)
                projects.append(p)

            return projects
        except SQLAlchemyError as e:
            raise DatabaseOperationFailedException("get projects list") from e

    @staticmethod
    async def get_total_count_by_user(
            db: AsyncSession, user_id: int, search: Optional[str] = None
    ) -> int:
        """
        获取指定用户的项目总数（用于分页）。

        Args:
            db (AsyncSession): SQLAlchemy异步数据库会话。
            user_id (int): 用户的唯一标识ID。
            search (Optional[str], optional): 项目名称模糊搜索关键字。

        Returns:
            int: 满足条件的项目总数。

        Raises:
            DatabaseOperationFailedException: 数据库操作失败时抛出。
            SQLAlchemyError: SQLAlchemy底层异常。
        """
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
        """
        更改项目状态（用于软删除）。

        Args:
            db (AsyncSession): 数据库会话。
            project_id (int): 项目ID。
            status (str): 新的项目状态。

        Returns:
            Optional[Project]: 更新后的项目对象或 None。
        """
        return await CRUDProject.update(db, project_id, project_status=status)


crud_project = CRUDProject()
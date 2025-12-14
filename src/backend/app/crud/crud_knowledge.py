"""
知识库 CRUD。

本模块提供领域知识（术语）管理的 CRUD 操作。
"""

# backend/app/crud/crud_knowledge.py

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, delete
from sqlalchemy.exc import SQLAlchemyError

from models.domain_knowledge import DomainKnowledge
from core.exceptions import DatabaseOperationFailedException


class CRUDKnowledge:
    """
    知识库（术语）数据操作类。

    提供领域知识/术语的增删改查及批量操作功能。
    """

    @staticmethod
    async def create(db: AsyncSession, project_id: int, **kwargs) -> DomainKnowledge:
        """
        创建单个术语。

        Args:
            db (AsyncSession): 数据库会话。
            project_id (int): 项目 ID。
            **kwargs: 术语字段。

        Returns:
            DomainKnowledge: 创建的术语对象。

        Raises:
            DatabaseOperationFailedException: 创建失败时抛出。
        """
        try:
            db_obj = DomainKnowledge(project_id=project_id, **kwargs)
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)
            return db_obj
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseOperationFailedException("create knowledge") from e

    @staticmethod
    async def get_by_project(
            db: AsyncSession,
            project_id: int,
            skip: int = 0,
            limit: int = 20,
            search: Optional[str] = None
    ) -> List[DomainKnowledge]:
        """
        获取项目下的术语列表 (支持搜索和分页)。

        Args:
            db (AsyncSession): 数据库会话。
            project_id (int): 项目 ID。
            skip (int): 跳过的记录数。
            limit (int): 返回的最大记录数。
            search (Optional[str]): 搜索关键字（术语名称）。

        Returns:
            List[DomainKnowledge]: 术语列表。

        Raises:
            DatabaseOperationFailedException: 查询失败时抛出。
        """
        try:
            query = select(DomainKnowledge).where(DomainKnowledge.project_id == project_id)

            if search:
                query = query.where(DomainKnowledge.term.ilike(f"%{search}%"))

            query = query.order_by(DomainKnowledge.created_at.desc()).offset(skip).limit(limit)
            result = await db.execute(query)
            return result.scalars().all()
        except SQLAlchemyError as e:
            raise DatabaseOperationFailedException("get knowledge list") from e

    @staticmethod
    async def get_total_count(db: AsyncSession, project_id: int, search: Optional[str] = None) -> int:
        """
        获取总数。

        Args:
            db (AsyncSession): 数据库会话。
            project_id (int): 项目 ID。
            search (Optional[str]): 搜索关键字。

        Returns:
            int: 记录总数。

        Raises:
            DatabaseOperationFailedException: 查询失败时抛出。
        """
        try:
            query = select(func.count(DomainKnowledge.knowledge_id)).where(DomainKnowledge.project_id == project_id)
            if search:
                query = query.where(DomainKnowledge.term.ilike(f"%{search}%"))
            result = await db.execute(query)
            return result.scalar_one()
        except SQLAlchemyError as e:
            raise DatabaseOperationFailedException("get knowledge count") from e

    @staticmethod
    async def get_all_by_project(db: AsyncSession, project_id: int) -> List[DomainKnowledge]:
        """
        获取项目下所有术语 (用于导出)。

        Args:
            db (AsyncSession): 数据库会话。
            project_id (int): 项目 ID。

        Returns:
            List[DomainKnowledge]: 所有术语列表。

        Raises:
            DatabaseOperationFailedException: 查询失败时抛出。
        """
        try:
            query = select(DomainKnowledge).where(DomainKnowledge.project_id == project_id)
            result = await db.execute(query)
            return result.scalars().all()
        except SQLAlchemyError as e:
            raise DatabaseOperationFailedException("get all knowledge") from e

    # 更新单条术语
    @staticmethod
    async def update(db: AsyncSession, db_obj: DomainKnowledge, update_data: dict) -> DomainKnowledge:
        """
        更新单条术语。

        Args:
            db (AsyncSession): 数据库会话。
            db_obj (DomainKnowledge): 要更新的术语对象。
            update_data (dict): 更新的数据字典。

        Returns:
            DomainKnowledge: 更新后的术语对象。

        Raises:
            DatabaseOperationFailedException: 更新失败时抛出。
        """
        try:
            for field,value in update_data.items():
                setattr(db_obj, field, value)
            await db.commit()
            await db.refresh(db_obj)
            await db.refresh(db_obj)
            return db_obj
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseOperationFailedException("update knowledge") from e

    # 删除单条术语
    @staticmethod
    async def delete(db: AsyncSession, knowledge_id: int) -> bool:
        """
        删除单条术语。

        Args:
            db (AsyncSession): 数据库会话。
            knowledge_id (int): 术语 ID。

        Returns:
            bool: 删除成功返回 True。

        Raises:
            DatabaseOperationFailedException: 删除失败时抛出。
        """
        try:
            query = delete(DomainKnowledge).where(DomainKnowledge.knowledge_id == knowledge_id)
            result = await db.execute(query)
            await db.commit()
            return result.rowcount > 0
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseOperationFailedException("delete knowledge") from e

    # 批量删除术语
    @staticmethod
    async def remove_multi(db: AsyncSession, project_id: int, ids: List[int]) -> int:
        """
        批量删除术语。

        Args:
            db (AsyncSession): 数据库会话。
            project_id (int): 项目 ID。
            ids (List[int]): 要删除的术语 ID 列表。

        Returns:
            int: 成功删除的记录数。

        Raises:
            DatabaseOperationFailedException: 删除失败时抛出。
        """
        try :
            query = delete(DomainKnowledge).where(
                DomainKnowledge.knowledge_id.in_(ids),
                DomainKnowledge.project_id == project_id
            )
            result = await db.execute(query)
            await db.commit()
            return result.rowcount
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseOperationFailedException("batch delete knowledge") from e

    # 通过ID查找单条术语
    @staticmethod
    async def get(db: AsyncSession, knowledge_id: int) -> Optional[DomainKnowledge]:
        """
        通过 ID 查找单条术语。

        Args:
            db (AsyncSession): 数据库会话。
            knowledge_id (int): 术语 ID。

        Returns:
            Optional[DomainKnowledge]: 术语对象或 None。
        """
        result = await db.execute(select(DomainKnowledge).where(DomainKnowledge.knowledge_id == knowledge_id))
        return result.scalar_one()

    @staticmethod
    async def batch_create(db: AsyncSession, project_id: int, items: List[dict]) -> int:
        """
        批量创建术语 (用于导入)。

        Args:
            db (AsyncSession): 数据库会话。
            project_id (int): 项目 ID。
            items (List[dict]): 术语数据列表。

        Returns:
            int: 创建的记录数。

        Raises:
            DatabaseOperationFailedException: 创建失败时抛出。
        """
        try:
            # 转换为 ORM 对象列表
            db_objs = [DomainKnowledge(project_id=project_id, **item) for item in items]
            db.add_all(db_objs)
            await db.commit()
            return len(db_objs)
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseOperationFailedException("batch create knowledge") from e

    @staticmethod
    async def check_term_exists(db: AsyncSession, project_id: int, term: str) -> bool:
        """
        检查术语是否存在。

        Args:
            db (AsyncSession): 数据库会话。
            project_id (int): 项目 ID。
            term (str): 术语名称。

        Returns:
            bool: 存在返回 True，否则返回 False。
        """
        query = select(DomainKnowledge).where(
            DomainKnowledge.project_id == project_id,
            DomainKnowledge.term == term
        )
        result = await db.execute(query)
        return result.scalar_one_or_none() is not None


crud_knowledge = CRUDKnowledge()

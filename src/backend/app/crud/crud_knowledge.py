# backend/app/crud/crud_knowledge.py

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, or_
from sqlalchemy.exc import SQLAlchemyError

from models.domain_knowledge import DomainKnowledge
from core.exceptions import DatabaseOperationFailedException


class CRUDKnowledge:
    @staticmethod
    async def create(db: AsyncSession, project_id: int, **kwargs) -> DomainKnowledge:
        """创建单个术语"""
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
        """获取项目下的术语列表 (支持搜索和分页)"""
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
        """获取总数"""
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
        """获取项目下所有术语 (用于导出)"""
        try:
            query = select(DomainKnowledge).where(DomainKnowledge.project_id == project_id)
            result = await db.execute(query)
            return result.scalars().all()
        except SQLAlchemyError as e:
            raise DatabaseOperationFailedException("get all knowledge") from e

    @staticmethod
    async def batch_create(db: AsyncSession, project_id: int, items: List[dict]) -> int:
        """批量创建术语 (用于导入)"""
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
        """检查术语是否存在"""
        query = select(DomainKnowledge).where(
            DomainKnowledge.project_id == project_id,
            DomainKnowledge.term == term
        )
        result = await db.execute(query)
        return result.scalar_one_or_none() is not None


crud_knowledge = CRUDKnowledge()
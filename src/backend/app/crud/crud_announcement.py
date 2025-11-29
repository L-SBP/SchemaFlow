# backend/app/crud/crud_announcement.py

from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete
from sqlalchemy.exc import SQLAlchemyError
from models.system_announcement import SystemAnnouncement as Announcement # 假设 ORM 模型名是 SystemAnnouncement
from core.exceptions import DatabaseOperationFailedException

class CRUDAnnouncement:
    @staticmethod
    async def create(db: AsyncSession, **kwargs) -> Announcement:
        """创建新公告 (4.2.1)"""
        try:
            db_obj = Announcement(**kwargs)
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)
            return db_obj
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseOperationFailedException("create announcement") from e

    @staticmethod
    async def update(db: AsyncSession, announcement_id: int, update_data: Dict[str, Any]) -> Optional[Announcement]:
        """更新公告 (4.2.2)"""
        try:
            query = update(Announcement).where(Announcement.announcement_id == announcement_id).values(**update_data).returning(Announcement)
            result = await db.execute(query)
            updated_announcement = result.scalar_one_or_none()
            await db.commit()
            return updated_announcement
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseOperationFailedException("update announcement") from e

    @staticmethod
    async def remove(db: AsyncSession, announcement_id: int) -> bool:
        """删除公告 (4.2.3)"""
        try:
            query = delete(Announcement).where(Announcement.announcement_id == announcement_id)
            result = await db.execute(query)
            await db.commit()
            return result.rowcount > 0
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseOperationFailedException("delete announcement") from e

curd_announcement = CRUDAnnouncement()
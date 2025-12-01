from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.exc import SQLAlchemyError

from models.system_announcement import SystemAnnouncement as Announcement
from core.exceptions import DatabaseOperationFailedException


class CRUDAnnouncement:

    @staticmethod
    async def get_list(
        db: AsyncSession,
        status: str | None,
        page: int,
        page_size: int
    ):
        """获取公告列表（用户端使用）"""
        query = select(Announcement)

        if status:
            query = query.where(Announcement.status == status)

        # total count
        count_query = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_query)).scalar()

        # pagination
        query = (
            query.order_by(Announcement.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        rows = (await db.execute(query)).scalars().all()
        return total, rows
    
    async def get(self, db: AsyncSession, announcement_id: int):
        """获取公告详情"""
        query = select(Announcement).where(Announcement.announcement_id == announcement_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def create(db: AsyncSession, **kwargs) -> Announcement:
        try:
            obj = Announcement(**kwargs)
            db.add(obj)
            await db.commit()
            await db.refresh(obj)
            return obj
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseOperationFailedException("create announcement") from e

    @staticmethod
    async def update(db: AsyncSession, announcement_id: int, update_data: Dict[str, Any]):
        try:
            query = (
                update(Announcement)
                .where(Announcement.announcement_id == announcement_id)
                .values(**update_data)
                .returning(Announcement)
            )
            result = await db.execute(query)
            obj = result.scalar_one_or_none()
            await db.commit()
            return obj
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseOperationFailedException("update announcement") from e

    @staticmethod
    async def remove(db: AsyncSession, announcement_id: int) -> bool:
        try:
            query = delete(Announcement).where(
                Announcement.announcement_id == announcement_id
            )
            result = await db.execute(query)
            await db.commit()
            return result.rowcount > 0
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseOperationFailedException("delete announcement") from e


# 正确实例名称
crud_announcement = CRUDAnnouncement()

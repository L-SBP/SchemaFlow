"""
公告 CRUD。

本模块提供系统公告的 CRUD 操作。
"""

# backend/app/crud/crud_announcement.py

from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.exc import SQLAlchemyError

from models.system_announcement import SystemAnnouncement as Announcement
from core.exceptions import DatabaseOperationFailedException


class CRUDAnnouncement:
    """
    公告数据操作类。

    提供系统公告的增删改查功能。
    """

    @staticmethod
    async def get_list(
        db: AsyncSession,
        status: str | None,
        page: int,
        page_size: int
    ):
        """
        获取公告列表（用户端使用）。

        Args:
            db (AsyncSession): 数据库会话。
            status (str | None): 公告状态筛选。
            page (int): 页码。
            page_size (int): 每页数量。

        Returns:
            Tuple[int, List[Announcement]]: (总记录数, 公告列表)。
        """
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
        """
        获取公告详情。

        Args:
            db (AsyncSession): 数据库会话。
            announcement_id (int): 公告 ID。

        Returns:
            Optional[Announcement]: 公告对象或 None。
        """
        query = select(Announcement).where(Announcement.announcement_id == announcement_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def create(db: AsyncSession, **kwargs) -> Announcement:
        """
        创建新公告。

        Args:
            db (AsyncSession): 数据库会话。
            **kwargs: 公告字段。

        Returns:
            Announcement: 创建的公告对象。

        Raises:
            DatabaseOperationFailedException: 创建失败时抛出。
        """
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
        """
        更新公告。

        Args:
            db (AsyncSession): 数据库会话。
            announcement_id (int): 公告 ID。
            update_data (Dict[str, Any]): 更新的数据字典。

        Returns:
            Optional[Announcement]: 更新后的公告对象或 None。

        Raises:
            DatabaseOperationFailedException: 更新失败时抛出。
        """
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
        """
        删除公告。

        Args:
            db (AsyncSession): 数据库会话。
            announcement_id (int): 公告 ID。

        Returns:
            bool: 删除成功返回 True，否则返回 False。

        Raises:
            DatabaseOperationFailedException: 删除失败时抛出。
        """
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

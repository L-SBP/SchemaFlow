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
from service.announcement_cache_service import AnnouncementCacheService


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
        # 只对已发布的公告启用缓存
        if status == "published":
            # 尝试从缓存获取
            cached_result = await AnnouncementCacheService.get_list_from_cache(page, page_size)
            if cached_result:
                total, items = cached_result
                # 将字典转换回对象
                announcements = []
                for item in items:
                    announcement = Announcement()
                    announcement.announcement_id = item["announcement_id"]
                    announcement.title = item["title"]
                    announcement.content = item["content"]
                    announcement.status = item["status"]
                    announcement.created_by = item["created_by"]
                    announcement.created_at = item["created_at"]
                    announcement.updated_at = item["updated_at"]
                    announcements.append(announcement)
                return total, announcements

        # 缓存未命中，从数据库查询
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

        # 如果是已发布的公告，缓存结果
        if status == "published" and rows:
            # 转换为字典格式用于缓存
            items = []
            for row in rows:
                item = {
                    "announcement_id": row.announcement_id,
                    "title": row.title,
                    "content": row.content,
                    "status": row.status,
                    "created_by": row.created_by,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                    "updated_at": row.updated_at.isoformat() if row.updated_at else None
                }
                items.append(item)

            # 设置缓存
            await AnnouncementCacheService.set_list_to_cache(page, page_size, total, items)

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
        # 尝试从缓存获取
        cached_data = await AnnouncementCacheService.get_detail_from_cache(announcement_id)
        if cached_data:
            # 将字典转换回对象
            announcement = Announcement()
            announcement.announcement_id = cached_data["announcement_id"]
            announcement.title = cached_data["title"]
            announcement.content = cached_data["content"]
            announcement.status = cached_data["status"]
            announcement.created_by = cached_data["created_by"]
            announcement.created_at = cached_data["created_at"]
            announcement.updated_at = cached_data["updated_at"]
            return announcement

        # 缓存未命中，从数据库查询
        query = select(Announcement).where(Announcement.announcement_id == announcement_id)
        result = await db.execute(query)
        announcement = result.scalar_one_or_none()

        # 如果查询到公告且状态为已发布，缓存结果
        if announcement and announcement.status == "published":
            announcement_data = {
                "announcement_id": announcement.announcement_id,
                "title": announcement.title,
                "content": announcement.content,
                "status": announcement.status,
                "created_by": announcement.created_by,
                "created_at": announcement.created_at.isoformat() if announcement.created_at else None,
                "updated_at": announcement.updated_at.isoformat() if announcement.updated_at else None
            }
            await AnnouncementCacheService.set_detail_to_cache(announcement_id, announcement_data)

        return announcement

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

            # 如果是已发布的公告，清除列表缓存
            if kwargs.get("status") == "published":
                await AnnouncementCacheService.invalidate_list_cache()

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

            # 如果公告状态或内容发生变化，清除相关缓存
            if obj:
                # 清除列表缓存
                await AnnouncementCacheService.invalidate_list_cache()
                # 清除详情缓存
                await AnnouncementCacheService.invalidate_detail_cache(announcement_id)

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

            # 清除相关缓存
            if result.rowcount > 0:
                # 清除列表缓存
                await AnnouncementCacheService.invalidate_list_cache()
                # 清除详情缓存
                await AnnouncementCacheService.invalidate_detail_cache(announcement_id)

            return result.rowcount > 0
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseOperationFailedException("delete announcement") from e


# 正确实例名称
crud_announcement = CRUDAnnouncement()

"""
公告服务。

为用户侧提供公告列表与详情的只读访问；创建与更新由管理员服务处理。
"""

# backend/app/service/announcement_service.py

from sqlalchemy.ext.asyncio import AsyncSession
from crud.crud_announcement import crud_announcement
from typing import Any, Dict


class AnnouncementService:
    """
    公告查询服务。

    提供公告列表与详情的读取方法，适用于用户端展示。
    """

    @staticmethod
    async def get_announcement_list(
        db: AsyncSession,
        status: str | None,
        page: int,
        page_size: int
    ) -> Dict[str, Any]:
        """
        获取公告列表。

        Args:
            db (AsyncSession): 数据库会话。
            status (str | None): 公告状态过滤。
            page (int): 页码。
            page_size (int): 每页数量。

        Returns:
            dict: 包含分页信息与公告条目的字典。
        """
        total, items = await crud_announcement.get_list(
            db=db,
            status=status,
            page=page,
            page_size=page_size
        )

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": items
        }

    @staticmethod
    async def get_announcement_detail(
        db: AsyncSession,
        announcement_id: int
    ) -> Any:
        """
        获取公告详情。

        Args:
            db (AsyncSession): 数据库会话。
            announcement_id (int): 公告 ID。

        Returns:
            Any: 公告 ORM 对象或序列化结果。
        """
        announcement = await crud_announcement.get(db, announcement_id)
        return announcement


# 单例实例
announcement_service = AnnouncementService()

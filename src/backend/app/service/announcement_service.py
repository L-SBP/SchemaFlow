from sqlalchemy.ext.asyncio import AsyncSession
from crud.crud_announcement import crud_announcement


class AnnouncementService:

    @staticmethod
    async def get_announcement_list(
        db: AsyncSession,
        status: str | None,
        page: int,
        page_size: int
    ):
        """
        获取公告列表
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
    ):
        """
        获取公告详情
        """
        announcement = await crud_announcement.get(db, announcement_id)
        return announcement


# 单例实例
announcement_service = AnnouncementService()

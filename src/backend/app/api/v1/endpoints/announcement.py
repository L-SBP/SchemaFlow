"""
公告 API 端点。

提供已发布公告的列表查询和详情获取接口，供登录用户使用。
"""

from typing import Any
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.deps import get_db, get_current_active_user
from schema.user import UserMe
from crud.crud_announcement import crud_announcement
from schema.announcement import (
    AnnouncementListResponse,
    AnnouncementDetailResponse
)

router = APIRouter()


# ============================
# 1. 获取公告列表（登录用户）
# ============================
@router.get(
    "/",
    response_model=AnnouncementListResponse,
    summary="获取公告列表"
)
async def read_announcements(
    db: AsyncSession = Depends(get_db),
    current_user: UserMe = Depends(get_current_active_user),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
):
    """
    获取已发布的系统公告（仅限登录用户）。

    Args:
        db (AsyncSession): 数据库会话。
        current_user (UserMe): 当前登录用户。
        page (int): 页码。
        page_size (int): 每页数量。

    Returns:
        AnnouncementListResponse: 公告列表响应。
    """
    total, items = await crud_announcement.get_list(
        db=db,
        status="published",
        page=page,
        page_size=page_size
    )

    return AnnouncementListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=items
    )


# ============================
# 2. 获取公告详情（登录用户）
# ============================
@router.get(
    "/{announcement_id}",
    response_model=AnnouncementDetailResponse,
    summary="获取公告详情"
)
async def get_announcement_detail(
    announcement_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserMe = Depends(get_current_active_user),
):
    """
    获取公告详情（仅限已发布公告）。

    Args:
        announcement_id (int): 公告 ID。
        db (AsyncSession): 数据库会话。
        current_user (UserMe): 当前登录用户。

    Returns:
        AnnouncementDetailResponse: 公告详情。

    Raises:
        HTTPException: 公告不存在(404)或未发布(403)。
    """
    announcement = await crud_announcement.get(db, announcement_id)

    if not announcement:
        raise HTTPException(status_code=404, detail="Announcement not found")

    if announcement.status != "published":
        raise HTTPException(status_code=403, detail="Announcement not published")

    return announcement

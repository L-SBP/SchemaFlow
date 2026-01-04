"""
系统公告 Schema。

本模块定义了系统公告的创建、更新、查询及响应模型。
用于管理员发布通知和用户查看公告。
"""

# backend/app/schema/announcement.py

from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import List, Optional


class AnnouncementBase(BaseModel):
    """
    公告基础 Schema。

    Attributes:
        title (str): 公告标题。
        content (str): 公告内容。
        status (str): 公告状态。
    """
    title: str
    content: str
    status: str


class AnnouncementResponse(BaseModel):
    """
    公告响应 Schema。

    Attributes:
        announcement_id (int): 公告 ID。
        title (str): 公告标题。
        content (str): 公告内容。
        status (str): 公告状态。
        created_at (datetime): 创建时间。
        updated_at (Optional[datetime]): 更新时间。
        created_by (Optional[int]): 创建人 ID。
    """
    announcement_id: int
    title: str
    content: str
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None

    # Pydantic v2 版本的 orm_mode
    model_config = ConfigDict(from_attributes=True)


class AnnouncementListResponse(BaseModel):
    """
    公告列表响应 Schema。

    Attributes:
        total (int): 总记录数。
        page (int): 当前页码。
        page_size (int): 每页数量。
        items (List[AnnouncementResponse]): 公告列表。
    """
    total: int
    page: int
    page_size: int
    items: List[AnnouncementResponse]

    model_config = ConfigDict(from_attributes=True)


class AnnouncementDetailResponse(AnnouncementResponse):
    """
    公告详情 Schema。
    """
    model_config = ConfigDict(from_attributes=True)

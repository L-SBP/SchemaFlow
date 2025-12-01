from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import List


class AnnouncementBase(BaseModel):
    title: str
    content: str
    status: str


class AnnouncementResponse(BaseModel):
    announcement_id: int
    title: str
    content: str
    status: str
    created_at: datetime

    # Pydantic v2 版本的 orm_mode
    model_config = ConfigDict(from_attributes=True)


class AnnouncementListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[AnnouncementResponse]

    model_config = ConfigDict(from_attributes=True)


class AnnouncementDetailResponse(AnnouncementResponse):
    """公告详情"""
    model_config = ConfigDict(from_attributes=True)

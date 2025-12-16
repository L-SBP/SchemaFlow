"""
系统公告模型。

本模块定义了用于存储系统公告信息的 ORM 模型。
"""

# backend/app/models/system_announcement.py

from sqlalchemy import Column, Text, String, Integer, Index, CheckConstraint, ForeignKey, DateTime
from sqlalchemy.sql import func
from core.database import Base

class SystemAnnouncement(Base):
    """
    系统公告表 ORM 模型。

    存储管理员发布的系统通知。

    Attributes:
        announcement_id (int): 公告唯一ID。
        title (str): 公告标题。
        content (str): 公告内容。
        status (str): 公告状态：draft/published/unpublished/expired。
        created_by (int): 创建人（管理员user_id）。
        created_at (datetime): 公告发布时间。
        updated_at (datetime): 最后更新时间。
    """
    __tablename__ = 'system_announcement'

    __table_args__ = (
        CheckConstraint("status IN ('draft', 'published', 'unpublished', 'expired')", name='ck_announcement_status'),
        Index('idx_announcements_created_by', 'created_by'),
        {'comment': '系统公告表，存储管理员发布的系统通知'}
    )

    announcement_id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment='公告唯一ID'
    )
    title = Column(
        String(200),
        nullable=False,
        comment='公告标题'
    )
    content = Column(
        Text,
        nullable=False,
        comment='公告内容'
    )
    status = Column(
        String(20),
        default='draft',
        nullable=False,
        comment='公告状态：draft(草稿)、published(已发布)、unpublished(已下架)、expired(已过期)'
    )
    created_by = Column(
        Integer,
        ForeignKey('user_account.user_id', ondelete='RESTRICT'),
        nullable=False,
        comment='创建人（管理员user_id）'
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment='公告发布时间'
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=True,
        comment='最后更新时间'
    )
    class Config:
        from_attributes = True
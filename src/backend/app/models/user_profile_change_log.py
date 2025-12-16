"""
资料变更日志模型。

本模块定义了用于记录用户个人资料修改历史的 ORM 模型。
"""

# backend/app/models/user_profile_change_log.py

from sqlalchemy import Column, Integer, CheckConstraint, Text, DateTime, String, ForeignKey, Index
from sqlalchemy.sql import func

from core.database import Base

class UserProfileChangeLog(Base):
    """
    用户资料变更历史记录表 ORM 模型。

    Attributes:
        change_id (int): 变更ID。
        user_id (int): 被修改的用户ID。
        change_type (str): 变更类型。
        old_value (str): 变更前的值。
        new_value (str): 变更后的值。
        created_at (datetime): 变更时间。
        ip_address (str): 操作IP地址。
        user_agent (str): 操作设备信息。
    """
    __tablename__ = "user_profile_change_log"

    __table_args__ = (
        CheckConstraint("change_type IN ('username', 'email', 'password', 'avatar', 'max_databases')"),
        Index("idx_change_logs_user_id", "user_id"),
        Index("idx_change_logs_type", "change_type"),
        Index("idx_change_logs_time", "created_at"),
        {'comment': '用户资料变更历史记录表'}
    )

    change_id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment='变更ID'
    )
    user_id = Column(
        Integer,
        # users -> user_account
        ForeignKey("user_account.user_id", ondelete="CASCADE"),
        nullable=False,
        comment='被修改的用户ID'
    )
    change_type = Column(
        Text,
        nullable=False,
        comment='变更类型'
    )
    old_value = Column(
        Text,
        nullable=True,
        comment='变更前的值'
    )
    new_value = Column(
        Text,
        nullable=False,
        comment='变更后的值'
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment='变更时间'
    )
    ip_address = Column(
        String(45),
        nullable=False,
        comment='操作IP地址'
    )
    user_agent = Column(
        Text,
        nullable=False,
        comment='操作设备信息'
    )
    class Config:
        from_attributes = True
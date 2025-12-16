"""
封禁日志模型。

本模块定义了用于存储用户账号封禁操作记录的 ORM 模型。
"""

# backend/app/models/user_ban_log.py

from sqlalchemy import Column, Integer, Text, CheckConstraint, DateTime, ForeignKey, Index
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import INTERVAL

from core.database import Base

class UserBanLog(Base):
    """
    封禁操作日志表 ORM 模型。

    Attributes:
        log_id (int): 日志ID。
        target_user_id (int): 被封禁的用户ID。
        admin_user_id (int): 执行操作的管理员ID。
        action_type (str): 操作类型：ban/unban/warning。
        reason (str): 封禁/解封原因。
        duration (interval): 封禁持续时间。
        effective_time (datetime): 生效时间。
        expiry_time (datetime): 过期时间。
        created_at (datetime): 记录创建时间。
    """
    __tablename__ = "user_ban_log"

    __table_args__ = (
        CheckConstraint("action_type IN ('ban', 'unban', 'warning')"),
        Index("idx_ban_logs_target_user", "target_user_id"),
        Index("idx_ban_logs_admin_user", "admin_user_id"),
        Index("idx_ban_logs_time", "effective_time"),
        {"comment": "封禁操作日志表"}
    )

    log_id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="日志ID"
    )
    target_user_id = Column(
        Integer,
        ForeignKey("user_account.user_id", ondelete="CASCADE"),
        nullable=False,
        comment="被封禁的用户ID"
    )
    admin_user_id = Column(
        Integer,
        ForeignKey("user_account.user_id", ondelete="RESTRICT"),
        nullable=False,
        comment="执行操作的管理员ID"
    )
    action_type = Column(
        Text,
        nullable=False,
        comment="操作类型：ban/unban/warning"
    )
    reason = Column(
        Text,
        nullable=False,
        comment="封禁/解封原因"
    )
    duration = Column(
        INTERVAL,
        nullable=True,
        comment="封禁持续时间"
    )
    effective_time = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="生效时间"
    )
    expiry_time = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="过期时间"
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="记录创建时间"
    )
    class Config:
        from_attributes = True
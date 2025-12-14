"""
消息模型。

本模块定义了用于存储用户与 AI 对话内容的 ORM 模型。
"""

# backend/app/models/message.py

from sqlalchemy import Column, Integer, Text, Boolean, CheckConstraint, Index, DateTime, ForeignKey
from sqlalchemy.sql import func

from core.database import Base

class Message(Base):
    """
    消息记录表 ORM 模型。

    存储用户与 AI 的对话内容。

    Attributes:
        message_id (int): 消息ID。
        session_id (int): 所属会话ID。
        message_type (str): 消息类型：user/assistant/system。
        content (str): 原始文本内容。
        requires_confirmation (bool): 是否需要用户确认。
        user_confirmed (bool): 用户是否确认执行。
        created_at (datetime): 创建时间。
    """
    __tablename__ = 'message'

    __table_args__ = (
        CheckConstraint("message_type IN ('user', 'assistant', 'system')", name='ck_message_type'),
        Index('idx_messages_session_id_created', 'session_id', 'created_at'),
        Index('idx_messages_message_type', 'message_type'),
        {'comment': '消息记录表，存储对话内容'}
    )

    message_id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment='消息ID'
    )
    session_id = Column(
        Integer,
        ForeignKey('session.session_id', ondelete='CASCADE'),
        nullable=False,
        comment='所属会话'
    )
    message_type = Column(
        Text,
        nullable=False,
        comment='消息类型：user/assistant/system'
    )
    content = Column(
        Text,
        nullable=False,
        comment='原始文本内容'
    )
    requires_confirmation = Column(
        Boolean,
        default=False,
        comment='是否需要用户确认'
    )
    user_confirmed = Column(
        Boolean,
        default=False,
        comment='用户是否确认执行'
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment='创建时间'
    )
    class Config:
        from_attributes = True
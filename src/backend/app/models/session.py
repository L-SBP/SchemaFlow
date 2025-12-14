"""
会话模型。

本模块定义了用于存储用户聊天会话上下文的 ORM 模型。
"""

# backend/app/models/session.py

from sqlalchemy import Column, String, CheckConstraint, Index, Integer, ForeignKey, DateTime
from sqlalchemy.sql import func
from core.database import Base
from sqlalchemy.orm import relationship
class Session(Base):
    """
    会话表 ORM 模型。

    存储用户与 AI 的对话上下文。

    Attributes:
        session_id (int): 会话ID。
        project_id (int): 关联的项目ID。
        session_name (str): 会话名称。
        created_at (datetime): 创建时间。
        last_activity (datetime): 最后活动时间。
    """
    __tablename__ = 'session'

    __table_args__ = (
        Index('idx_sessions_project_id', 'project_id'),
        Index('idx_sessions_last_activity', 'last_activity'),
        {'comment': '会话表，存储用户与AI的对话上下文'}
    )

    session_id = Column(
        Integer,
        autoincrement=True,
        primary_key=True,
        comment='会话ID'
    )
    project_id = Column(
        Integer,
        ForeignKey('project.project_id', ondelete='CASCADE'),
        nullable=False,
        comment='关联的项目ID'
    )
    # 反向关联：让 Session 知道它属于哪个 Project
    project = relationship("Project", back_populates="sessions")
    session_name = Column(
        String(100),
        nullable=False,
        default='New Session',
        comment='会话名称'
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment='创建时间'
    )
    last_activity = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=True,
        comment='最后活动时间'
    )
    class Config:
        from_attributes = True
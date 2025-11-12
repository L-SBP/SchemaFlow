from sqlalchemy import Column, String, CheckConstraint, Index, Integer, ForeignKey, DateTime
from sqlalchemy.sql import func
from src.backend.app.core.database import Base

class Session(Base):
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
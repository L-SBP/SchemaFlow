from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.sql import func

from app.core.database import Base

class DomainKnowledge(Base):
    __tablename__ = 'domain_knowledge'

    __table_args__ = (
        Index('idx_domain_knowledge_project_id', 'project_id'),
        Index('idx_domain_knowledge_term', 'term'),
        {'comment': '用户专业知识表，增强AI对业务术语的理解'}
    )

    knowledge_id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment='知识条目ID'
    )
    project_id = Column(
        Integer,
        ForeignKey('project.project_id', ondelete='CASCADE'),
        nullable=False,
        comment='所属项目'
    )
    term = Column(
        String(100),
        nullable=False,
        comment='业务术语'
    )
    definition = Column(
        Text,
        nullable=False,
        comment='术语定义'
    )
    examples = Column(
        Text,
        comment='使用示例'
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment='创建时间'
    )
    class Config:
        from_attributes = True
"""
领域知识模型。

本模块定义了用于存储用户专业知识（术语）的 ORM 模型。
"""

# backend/app/models/domain_knowledge.py

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.sql import func

from core.database import Base

class DomainKnowledge(Base):
    """
    用户专业知识表 ORM 模型。

    增强 AI 对业务术语的理解。

    Attributes:
        knowledge_id (int): 知识条目ID。
        project_id (int): 所属项目ID。
        term (str): 业务术语。
        definition (str): 术语定义。
        examples (str): 使用示例。
        created_at (datetime): 创建时间。
    """
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
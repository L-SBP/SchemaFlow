from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.core.database import Base


class Project(Base):
    __tablename__ = 'project'

    # 表注释和约束
    __table_args__ = (
        CheckConstraint("project_status IN ('active', 'archived', 'deleted')", name='ck_project_status'),
        Index('idx_projects_user_id', 'user_id'),
        Index('idx_projects_status', 'project_status'),
        Index('idx_projects_updated_at', 'updated_at'),
        {'comment': '项目表，存储用户业务场景的逻辑定义'}
    )

    # 列定义
    project_id = Column(
        Integer,
        autoincrement=True,
        primary_key=True,
        comment='项目ID'
    )
    user_id = Column(
        Integer,
        ForeignKey('user_account.user_id', ondelete='CASCADE'),
        nullable=False,
        comment='所属用户'
    )
    instance_id = Column(
        Integer,
        ForeignKey('database_instance.instance_id', ondelete='RESTRICT'),
        nullable=False,
        comment='关联的数据库实例'
    )
    project_name = Column(
        String(100),
        nullable=False,
        comment='项目名称，如"我的服装店"'
    )
    description = Column(
        Text,
        nullable=True,
        comment='业务需求描述'
    )
    schema_definition = Column(
        JSONB,
        nullable=True,
        comment='AI生成的DDL结构（表、字段、约束等）'
    )
    project_status = Column(
        Text,
        default='active',
        nullable=False,
        comment='项目状态'
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment='创建时间'
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=True,
        comment='最后更新时间'
    )
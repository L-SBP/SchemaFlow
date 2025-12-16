"""
项目模型。

本模块定义了用于存储用户项目和业务逻辑定义的 ORM 模型。
"""

# backend/app/models/project.py

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from core.database import Base
from sqlalchemy.orm import relationship

class Project(Base):
    """
    项目表 ORM 模型，存储用户业务场景的逻辑定义。
    """
    __tablename__ = 'project'

    # 表注释和约束
    __table_args__ = (
        # 【保留你的修改】必须包含 'completed'，否则部署成功后改状态会报错
        CheckConstraint(
            "project_status IN ('active', 'initializing', 'pending_confirmation', 'deleted', 'completed')",
            name='ck_project_status'
        ),
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
    
    # 关联关系
    sessions = relationship("Session", back_populates="project", cascade="all, delete-orphan")
    
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
        comment='项目名称'
    )
    description = Column(
        Text,
        nullable=True,
        comment='业务需求描述'
    )
    schema_definition = Column(
        JSONB,
        nullable=True,
        comment='AI生成的Schema结构（JSON格式）'
    )

    ddl_statement = Column(
        Text,
        nullable=True,
        comment='AI生成的DDL建表语句'
    )

    # 👇【新增合并】这是你同学加的新字段，用于存 ER 图代码
    er_diagram_code = Column(
        Text,
        nullable=True,
        comment='AI生成的Mermaid ER图代码'
    )

    creation_stage = Column(
        String(50),
        default='initializing',
        nullable=False,
        comment='创建进度阶段 (initializing, generating_schema, schema_generated, generating_ddl, ddl_generated, executing_ddl, completed)'
    )

    project_status = Column(
        String(50), # 保留你的 String(50)，比 Text 更规范
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
    
    class Config:
        from_attributes = True
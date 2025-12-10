from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from core.database import Base


class Project(Base):
    """
    项目表 ORM 模型，存储用户业务场景的逻辑定义。

    Attributes:
        project_id (int): 项目ID。
        user_id (int): 所属用户ID。
        instance_id (int): 关联的数据库实例ID。
        project_name (str): 项目名称。
        description (str): 业务需求描述。
        schema_definition (dict): AI生成的DDL结构。
        project_status (str): 项目状态。
        created_at (datetime): 创建时间。
        updated_at (datetime): 最后更新时间。
    """
    __tablename__ = 'project'

    # 表注释和约束
    __table_args__ = (
        # [修复] 在列表中加入 'pending_confirmation'
        CheckConstraint(
            "project_status IN ('active', 'initializing', 'pending_confirmation', 'deleted')",
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
        comment='AI生成的Schema结构（JSON格式，包含schema文本和元数据）'
    )

    # --- 新增字段 ---
    ddl_statement = Column(
        Text,
        nullable=True,
        comment='AI生成的DDL语句'
    )
    # ----------------

    # --- 新增字段 ---
    creation_stage = Column(
        String(50),
        default='initializing',
        nullable=False,
        comment='创建进度阶段 (initializing, generating_schema, schema_generated, generating_ddl, ddl_generated, executing_ddl, completed)'
    )
    # ----------------

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
    class Config:
        from_attributes = True
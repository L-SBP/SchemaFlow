from sqlalchemy import Column, Integer, String, Text, DateTime, CheckConstraint, Index
from sqlalchemy.sql import func
from app.core.database import Base


class DatabaseInstance(Base):
    __tablename__ = 'database_instance'

    __table_args__ = (
        CheckConstraint("status IN ('active', 'inactive', 'error')", name='ck_database_status'),
        Index('idx_database_instances_status', 'status'),
        Index('idx_database_instances_last_used', 'last_used_at'),
        {'comment': '物理数据库实例元信息，存储连接凭证和状态'}
    )

    instance_id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment='实例ID'
    )
    db_type = Column(
        Text,
        nullable=False,
        default='mysql',
        comment='数据库类型'
    )
    db_host = Column(
        String(200),
        nullable=False,
        comment='数据库主机地址'
    )
    db_port = Column(
        Integer,
        default=3306,
        comment='端口'
    )
    db_name = Column(
        String(100),
        nullable=False,
        comment='数据库名'
    )
    db_username = Column(
        String(100),
        nullable=False,
        comment='用户名'
    )
    db_password = Column(
        String(255),
        nullable=False,
        comment='密码（加密存储）'
    )
    status = Column(
        Text,
        default='active',
        nullable=False,
        comment='实例状态'
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment='创建时间'
    )
    last_used_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=True,
        comment='最后使用时间'
    )
    class Config:
        from_attributes = True
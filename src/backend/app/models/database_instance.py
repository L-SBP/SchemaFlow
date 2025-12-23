"""
数据库实例模型。

本模块定义了用于存储物理数据库实例元信息的 ORM 模型。
"""

# backend/app/models/database_instance.py

from sqlalchemy import Column, Integer, String, Text, DateTime, CheckConstraint, Index, URL
from sqlalchemy.sql import func
from core.database import Base
from core.config import config


class DatabaseInstance(Base):
    """
    物理数据库实例元信息表 ORM 模型。

    存储数据库连接凭证和状态。

    Attributes:
        instance_id (int): 实例ID。
        db_type (str): 数据库类型。
        db_host (str): 数据库主机地址。
        db_port (int): 端口。
        db_name (str): 数据库名。
        db_username (str): 用户名。
        db_password (str): 密码（加密存储）。
        status (str): 实例状态。
        created_at (datetime): 创建时间。
        last_used_at (datetime): 最后使用时间。
    """
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

    @property
    def user_database_url(self) -> URL:
        """
        获取用户数据库连接 URL。

        Returns:
            URL: 用户数据库连接 URL。
        """
        if self.db_type == "mysql":
            drivername = config.mysql.driver
            return URL.create(
                drivername=drivername,
                username=self.db_username,
                password=self.db_password,
                host=self.db_host,
                port=self.db_port,
                database=self.db_name
            )
        elif self.db_type == "postgresql":
            drivername = config.postgresql.driver
            return URL.create(
                drivername=drivername,
                username=self.db_username,
                password=self.db_password,
                host=self.db_host,
                port=self.db_port,
                database=self.db_name
            )
        elif self.db_type == "sqlite":
            # SQLite是文件型数据库，只需要文件路径
            db_path = config.sqlite.db_path
            import os
            db_file_path = os.path.join(db_path, f"{self.db_name}.db")
            return URL.create(
                drivername=config.sqlite.driver,
                database=db_file_path
            )
        else:
            raise ValueError("Invalid database type")
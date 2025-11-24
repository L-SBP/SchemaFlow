from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, CheckConstraint, Index
from sqlalchemy.sql import func
from core.database import Base

class UserAccount(Base):
    __tablename__ = 'user_account'

    __table_args__ = (
        CheckConstraint("status IN ('normal', 'suspended', 'banned')", name='ck_user_status'),
        Index('idx_user_account_status', 'status'),
        Index('idx_user_account_email', 'email'),
        {'comment': '用户主表，存储所有注册用户的基本信息'}
    )
    
    user_id = Column(
        Integer,
        autoincrement=True,
        primary_key=True,
        index=True,
        comment='用户唯一ID'
    )

    username = Column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
        comment='用户名'
    )
    email = Column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
        comment='注册邮箱'
    )
    password_hash = Column(
        String(255),
        nullable=False,
        comment='加密后的密码'
    )
    status = Column(
        Text,
        default='normal',
        nullable=False,
        comment='账户状态：normal/suspended/banned'
    )
    used_databases = Column(
        Integer,
        default=0,
        nullable=False,
        comment='已使用的数据库项目数'
    )
    avatar_url = Column(
        Text,
        comment='头像图片URL'
    )
    is_admin = Column(
        Boolean,
        default=False,
        comment='是否为管理员'
    )
    max_databases = Column(
        Integer,
        default=10,
        comment='允许创建的最大数据库项目数'
    )
    last_login_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        comment='最后登录时间'
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment='注册时间'
    )
    class Config:
        from_attributes = True
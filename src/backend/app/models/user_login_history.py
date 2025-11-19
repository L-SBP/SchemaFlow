from sqlalchemy import Column, Text, String, Integer, Boolean, Index, CheckConstraint, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import INTERVAL, JSONB
from sqlalchemy.sql import func
from app.core.database import Base

class UserLoginHistory(Base):
    __tablename__ = "user_login_history"

    __table_args__ = (
        CheckConstraint("login_status IN ('success', 'failed', 'expired', 'forced_logout')", name='user_login_history_login_status_check'),
        Index('idx_login_history_user_id', 'user_id'),
        Index('idx_login_history_time_range', 'login_time'),
        Index('idx_login_history_ip', 'ip_address'),
        {'comment': '用户登录登出历史记录表'}
    )

    login_id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment='登录记录ID'
    )
    user_id = Column(
        Integer,
        ForeignKey('user_account.user_id', ondelete='CASCADE'),
        nullable=False,
        comment='用户ID'
    )
    login_time = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment='登录时间'
    )
    logout_time = Column(
        DateTime(timezone=True),
        nullable=True,
        comment='登出时间'
    )
    session_duration = Column(
        INTERVAL,
        nullable=True,
        comment='会话持续时间'
    )
    ip_address = Column(
        String(45),
        nullable=False,
        comment='登录IP地址'
    )
    user_agent = Column(
        Text,
        comment='浏览器/设备信息'
    )
    login_status = Column(
        Text,
        nullable=False,
        comment='登录状态：success/failed/expired/forced_logout'
    )
    failure_reason = Column(
        Text,
        comment='失败原因（仅当失败时）'
    )
    device_info = Column(
        JSONB,
        comment='详细设备信息（JSON格式）'
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment='记录创建时间'
    )
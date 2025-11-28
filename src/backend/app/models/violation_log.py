from sqlalchemy import Column, Text, String, Integer, DateTime, CheckConstraint, Index, ForeignKey
from sqlalchemy.sql import func

from core.database import Base

class ViolationLog(Base):
    __tablename__ = "violation_log"

    __table_args__ = (
        CheckConstraint("""event_type IN (
            'multiple_failed_logins',
            'suspicious_query',
            'frequent_remote_login',
            'ai_violation_content',
            'excessive_api_usage',
            'unauthorized_access_attempt',
            'sql_injection_attempt'
        )"""),
        CheckConstraint("risk_level IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')"),
        Index("idx_violation_logs_user_id", "user_id"),
        Index("idx_violation_logs_time", "created_at"),
        Index("idx_violation_logs_status", "resolution_status"),
        Index("idx_violation_logs_risk_level", "risk_level"),
        {'comment': '违规行为日志表'}
    )

    violation_id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment='违规行为ID'
    )
    user_id = Column(
        Integer,
        # 👇 修改点 1：users -> user_account
        ForeignKey('user_account.user_id', ondelete='CASCADE'),
        nullable=False,
        comment='违规用户ID'
    )
    event_type = Column(
        Text,
        nullable=False,
        comment='违规事件类型'
    )
    event_description = Column(
        Text,
        nullable=False,
        comment='事件详细描述'
    )
    risk_level = Column(
        Text,
        nullable=False,
        comment='风险等级：LOW/MEDIUM/HIGH/CRITICAL'
    )
    ip_address = Column(
        String(45),
        nullable=False,
        comment='违规操作IP地址'
    )
    client_user_agent = Column(
        Text,
        nullable=True,
        comment='客户端用户代理信息'
    )
    request_content = Column(
        Text,
        nullable=True,
        comment='原始请求内容'
    )
    handled_by = Column(
        Integer,
        # 👇 修改点 2：users -> user_account
        ForeignKey('user_account.user_id', ondelete='SET NULL'),
        nullable=True,
        comment='处理人ID'
    )
    handled_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment='处理时间'
    )
    resolution_status = Column(
        Text,
        default='pending',
        nullable=False,
        comment='处理状态：pending/resolved/rejected'
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment='记录创建时间'
    )
    class Config:
        from_attributes = True
from sqlalchemy import Column, Integer, DateTime, Text, ForeignKey, CheckConstraint, Index
from sqlalchemy.sql import func

from core.database import Base

class UnbanRequest(Base):
    __tablename__ = "unban_request"

    __table_args__ = (
        CheckConstraint("status IN ('pending', 'approved', 'rejected', 'processed')"),
        Index("idx_unban_requests_user", "user_id"),
        Index("idx_unban_requests_time", "request_time"),
        {'comment': '用户解封申请表'}
    )

    request_id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment='申请ID'
    )
    user_id = Column(
        Integer,
        ForeignKey('user_account.user_id', ondelete='CASCADE'),
        nullable=False,
        comment='申请用户ID'
    )
    ban_log_id = Column(
        Integer,
        ForeignKey('user_ban_log.log_id', ondelete='CASCADE'),
        nullable=False,
        comment='关联的封禁日志ID'
    )
    request_time = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment='申请时间'
    )
    reason = Column(
        Text,
        nullable=False,
        comment='申请解封理由'
    )
    supporting_evidence = Column(
        Text,
        comment='支持证据'
    )
    status = Column(
        Text,
        default='pending',
        nullable=False,
        comment='申请状态：pending/approved/rejected/processed'
    )
    admin_user_id = Column(
        Integer,
        # 👇 修改点：users -> user_account
        ForeignKey('user_account.user_id', ondelete='SET NULL'),
        comment='处理管理员ID'
    )
    decision_time = Column(
        DateTime(timezone=True),
        comment='处理时间'
    )
    decision_reason = Column(
        Text,
        comment='处理结果'
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment='记录创建时间'
    )
    class Config:
        from_attributes = True
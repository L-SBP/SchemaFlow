from sqlalchemy import Column, Integer, Text, String, Boolean, CheckConstraint, DateTime, ForeignKey, Index
from sqlalchemy.sql import func

from app.core.database import Base

class OperationLog(Base):
    __tablename__ = 'operation_log'

    __table_args__ = (
        CheckConstraint("operation_type IN ('INSERT', 'UPDATE', 'DELETE', 'ALTER', 'DROP', 'CREATE')", name='operation_log_operation_type_check'),
        CheckConstraint("status IN ('success', 'failed', 'cancelled')"),
        Index('idx_operation_logs_user_project', 'user_id', 'project_id'),
        Index('idx_operation_logs_executed_at', 'executed_at'),
        Index('idx_operation_logs_status', 'status'),
        {'comment': '操作审计日志表，记录所有数据变更操作'}
    )

    log_id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment='日志ID'
    )
    user_id = Column(
        Integer,
        ForeignKey('user_account.user_id', ondelete='RESTRICT'),
        nullable=False,
        comment='操作用户'
    )
    project_id = Column(
        Integer,
        ForeignKey('project.project_id', ondelete='CASCADE'),
        nullable=False,
        comment='所属项目'
    )
    session_id = Column(
        Integer,
        ForeignKey('session.session_id', ondelete='CASCADE'),
        nullable=False,
        comment='所属会话'
    )
    message_id = Column(
        Integer,
        ForeignKey('message.message_id', ondelete='CASCADE'),
        nullable=False,
        comment='触发操作的消息'
    )
    statement_id = Column(
        Integer,
        ForeignKey('ai_generated_statement.statement_id', ondelete='CASCADE'),
        nullable=False,
        comment='关联的SQL语句'
    )
    operation_type = Column(
        Text,
        nullable=False,
        comment='操作类型'
    )
    target_table = Column(
        String(100),
        nullable=False,
        comment='目标表名'
    )
    sql_statement = Column(
        Text,
        nullable=False,
        comment='完整SQL语句'
    )
    natural_language_intent = Column(
        Text,
        nullable=False,
        comment='用户原始指令'
    )
    status = Column(
        Text,
        nullable=False,
        comment='执行状态'
    )
    error_message = Column(
        Text,
        nullable=True,
        comment='错误信息（若失败）'
    )
    affected_rows = Column(
        Integer,
        default=0,
        comment='影响行数'
    )
    confirmed_by_user = Column(
        Boolean,
        default=False,
        comment='是否经用户确认'
    )
    executed_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment='执行时间'
    )
    execution_duration_ms = Column(
        Integer,
        comment='执行耗时（毫秒）'
    )
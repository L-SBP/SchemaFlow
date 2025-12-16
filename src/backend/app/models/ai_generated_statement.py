"""
AI 生成语句模型。

本模块定义了用于存储 AI 生成的 SQL 语句及其执行状态的 ORM 模型。
"""

# backend/app/models/ai_generated_statement.py

from sqlalchemy import Column, Text, Integer, Index, CheckConstraint, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from core.database import Base

class AIGeneratedStatement(Base):
    """
    AI生成的SQL语句明细表 ORM 模型。

    存储 AI 生成的 SQL 语句、执行状态及结果。

    Attributes:
        statement_id (int): 语句ID。
        message_id (int): 所属消息ID。
        statement_order (int): 语句执行顺序。
        sql_text (str): SQL语句文本。
        statement_type (str): 语句类型。
        execution_status (str): 执行状态。
        execution_result (dict): 执行结果。
        executed_at (datetime): 执行时间。
        created_at (datetime): 创建时间。
    """
    __tablename__ = "ai_generated_statement"

    __table_args__ = (
        CheckConstraint("statement_type IN ('SELECT', 'INSERT', 'UPDATE', 'DELETE', 'DDL', 'OTHER')", name='ai_generated_statement_type_check'),
        CheckConstraint("execution_status IN ('pending', 'completed', 'failed')", name='ai_generated_statement_status_check'),
        Index('idx_ai_statements_message_id', 'message_id'),
        {'comment': 'AI生成的SQL语句明细表'}
    )

    statement_id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        index=True,
        comment='语句ID'
    )
    message_id = Column(
        Integer,
        ForeignKey('message.message_id', ondelete='CASCADE'),
        nullable=False,
        comment='所属消息'
    )
    statement_order = Column(
        Integer,
        nullable=False,
        comment='语句执行顺序'
    )
    sql_text = Column(
        Text,
        nullable=False,
        comment='SQL语句文本'
    )
    statement_type = Column(
        Text,
        nullable=False,
        comment='语句类型'
    )
    execution_status = Column(
        Text,
        default='pending',
        nullable=False,
        comment='执行状态'
    )
    execution_result = Column(
        JSONB,
        comment='执行结果'
    )
    executed_at = Column(
        DateTime(timezone=True),
        comment='执行时间'
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment='创建时间'
    )
    class Config:
        from_attributes = True
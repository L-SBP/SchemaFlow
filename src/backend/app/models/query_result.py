"""
查询结果模型。

本模块定义了用于缓存 SQL 查询结果的 ORM 模型。
"""

# backend/app/models/query_result.py

from sqlalchemy import Column, Integer, Text, String, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from core.database import Base

class QueryResult(Base):
    """
    查询结果缓存表 ORM 模型。

    存储 SELECT 查询结果。

    Attributes:
        result_id (int): 结果ID。
        statement_id (int): 关联的SQL语句ID。
        result_data (dict): 查询结果数据（快照）。
        data_summary (str): AI生成的自然语言摘要。
        chart_type (str): 推荐图表类型。
        cached_at (datetime): 缓存时间。
    """
    __tablename__ = 'query_result'

    __table_args__ = (
        Index('idx_query_results_statement_id', 'statement_id'),
        Index('idx_query_results_cached_at', 'cached_at'),
        {'comment': '查询结果缓存表，存储SELECT查询结果'}
    )

    result_id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment='结果ID'
    )
    statement_id = Column(
        Integer,
        ForeignKey('ai_generated_statement.statement_id', ondelete='CASCADE'),
        nullable=False,
        comment='关联的SQL语句ID'
    )
    result_data = Column(
        JSONB,
        comment='查询结果数据（快照）'
    )
    data_summary = Column(
        Text,
        comment='AI生成的自然语言摘要'
    )
    chart_type = Column(
        String(50),
        comment='推荐图表类型（bar, line, pie等）'
    )
    cached_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment='缓存时间'
    )
    class Config:
        from_attributes = True
from sqlalchemy import Column, Integer, Text, String, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from core.database import Base

class QueryResult(Base):
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
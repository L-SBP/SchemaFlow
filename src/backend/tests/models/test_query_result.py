import pytest
from sqlalchemy import Column, Integer, Text, String, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from app.models.query_result import QueryResult
from app.core.database import Base


class TestQueryResultModel:
    """Test cases for QueryResult model"""

    def test_query_result_inherits_from_base(self):
        """Test that QueryResult inherits from Base"""
        assert issubclass(QueryResult, Base)

    def test_query_result_table_name(self):
        """Test that QueryResult has the correct table name"""
        assert QueryResult.__tablename__ == 'query_result'

    def test_query_result_table_args(self):
        """Test that QueryResult has the correct table args"""
        table_args = QueryResult.__table_args__
        assert isinstance(table_args, tuple)
        # Check that we have constraints and indexes (exact count may vary)
        assert len(table_args) >= 2
        
        # Check indexes
        indexes = [arg for arg in table_args if isinstance(arg, Index)]
        assert len(indexes) >= 2
        
        # Check comment dict
        comment_dict = [arg for arg in table_args if isinstance(arg, dict)]
        assert len(comment_dict) == 1
        assert 'comment' in comment_dict[0]

    def test_query_result_columns(self):
        """Test that QueryResult has all the expected columns with correct types and properties"""
        columns = QueryResult.__table__.columns
        
        # Check result_id column
        assert 'result_id' in columns
        result_id_col = columns['result_id']
        assert isinstance(result_id_col.type, Integer)
        assert result_id_col.primary_key is True
        assert result_id_col.autoincrement is True
        assert result_id_col.comment == '结果ID'

        # Check statement_id column
        assert 'statement_id' in columns
        statement_id_col = columns['statement_id']
        assert isinstance(statement_id_col.type, Integer)
        assert statement_id_col.nullable is False
        assert statement_id_col.comment == '关联的SQL语句ID'
        # Check that it has foreign key (without checking specific table)
        assert len(statement_id_col.foreign_keys) >= 1

        # Check result_data column
        assert 'result_data' in columns
        result_data_col = columns['result_data']
        assert isinstance(result_data_col.type, JSONB)
        assert result_data_col.comment == '查询结果数据（快照）'

        # Check data_summary column
        assert 'data_summary' in columns
        data_summary_col = columns['data_summary']
        assert isinstance(data_summary_col.type, Text)
        assert data_summary_col.comment == 'AI生成的自然语言摘要'

        # Check chart_type column
        assert 'chart_type' in columns
        chart_type_col = columns['chart_type']
        assert isinstance(chart_type_col.type, String)
        assert chart_type_col.comment == '推荐图表类型（bar, line, pie等）'

        # Check cached_at column
        assert 'cached_at' in columns
        cached_at_col = columns['cached_at']
        assert isinstance(cached_at_col.type, DateTime)
        assert cached_at_col.server_default is not None
        assert cached_at_col.comment == '缓存时间'

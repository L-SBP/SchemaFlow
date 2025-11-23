import pytest
from sqlalchemy import Column, Text, Integer, Index, CheckConstraint, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from app.models.ai_generated_statement import AIGeneratedStatement
from app.core.database import Base


class TestAIGeneratedStatementModel:
    """Test cases for AIGeneratedStatement model"""

    def test_ai_generated_statement_inherits_from_base(self):
        """Test that AIGeneratedStatement inherits from Base"""
        assert issubclass(AIGeneratedStatement, Base)

    def test_ai_generated_statement_table_name(self):
        """Test that AIGeneratedStatement has the correct table name"""
        assert AIGeneratedStatement.__tablename__ == 'ai_generated_statement'

    def test_ai_generated_statement_table_args(self):
        """Test that AIGeneratedStatement has the correct table args"""
        table_args = AIGeneratedStatement.__table_args__
        assert isinstance(table_args, tuple)
        # Check that we have constraints and indexes (exact count may vary)
        assert len(table_args) >= 2
        
        # Check constraints
        constraints = [arg for arg in table_args if isinstance(arg, CheckConstraint)]
        assert len(constraints) >= 2
        
        # Check indexes
        indexes = [arg for arg in table_args if isinstance(arg, Index)]
        assert len(indexes) >= 1
        
        # Check comment dict
        comment_dict = [arg for arg in table_args if isinstance(arg, dict)]
        assert len(comment_dict) == 1
        assert 'comment' in comment_dict[0]

    def test_ai_generated_statement_columns(self):
        """Test that AIGeneratedStatement has all the expected columns with correct types and properties"""
        columns = AIGeneratedStatement.__table__.columns
        
        # Check statement_id column
        assert 'statement_id' in columns
        statement_id_col = columns['statement_id']
        assert isinstance(statement_id_col.type, Integer)
        assert statement_id_col.primary_key is True
        assert statement_id_col.autoincrement is True
        assert statement_id_col.index is True
        assert statement_id_col.comment == '语句ID'

        # Check message_id column
        assert 'message_id' in columns
        message_id_col = columns['message_id']
        assert isinstance(message_id_col.type, Integer)
        assert message_id_col.nullable is False
        assert message_id_col.comment == '所属消息'
        # Check that it has foreign key (without checking specific table)
        assert len(message_id_col.foreign_keys) >= 1

        # Check statement_order column
        assert 'statement_order' in columns
        statement_order_col = columns['statement_order']
        assert isinstance(statement_order_col.type, Integer)
        assert statement_order_col.nullable is False
        assert statement_order_col.comment == '语句执行顺序'

        # Check sql_text column
        assert 'sql_text' in columns
        sql_text_col = columns['sql_text']
        assert isinstance(sql_text_col.type, Text)
        assert sql_text_col.nullable is False
        assert sql_text_col.comment == 'SQL语句文本'

        # Check statement_type column
        assert 'statement_type' in columns
        statement_type_col = columns['statement_type']
        assert isinstance(statement_type_col.type, Text)
        assert statement_type_col.nullable is False
        assert statement_type_col.comment == '语句类型'

        # Check execution_status column
        assert 'execution_status' in columns
        execution_status_col = columns['execution_status']
        assert isinstance(execution_status_col.type, Text)
        assert execution_status_col.default.arg == 'pending'
        assert execution_status_col.nullable is False
        assert execution_status_col.comment == '执行状态'

        # Check execution_result column
        assert 'execution_result' in columns
        execution_result_col = columns['execution_result']
        assert isinstance(execution_result_col.type, JSONB)
        assert execution_result_col.comment == '执行结果'

        # Check executed_at column
        assert 'executed_at' in columns
        executed_at_col = columns['executed_at']
        assert isinstance(executed_at_col.type, DateTime)
        assert executed_at_col.comment == '执行时间'

        # Check created_at column
        assert 'created_at' in columns
        created_at_col = columns['created_at']
        assert isinstance(created_at_col.type, DateTime)
        assert created_at_col.server_default is not None
        assert created_at_col.comment == '创建时间'

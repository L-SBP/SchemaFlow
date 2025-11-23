import pytest
from sqlalchemy import Column, Integer, Text, String, Boolean, CheckConstraint, DateTime, ForeignKey, Index
from sqlalchemy.sql import func

from app.models.operation_log import OperationLog
from app.core.database import Base


class TestOperationLogModel:
    """Test cases for OperationLog model"""

    def test_operation_log_inherits_from_base(self):
        """Test that OperationLog inherits from Base"""
        assert issubclass(OperationLog, Base)

    def test_operation_log_table_name(self):
        """Test that OperationLog has the correct table name"""
        assert OperationLog.__tablename__ == 'operation_log'

    def test_operation_log_table_args(self):
        """Test that OperationLog has the correct table args"""
        table_args = OperationLog.__table_args__
        assert isinstance(table_args, tuple)
        # Check that we have constraints and indexes (exact count may vary)
        assert len(table_args) >= 4
        
        # Check constraints
        constraints = [arg for arg in table_args if isinstance(arg, CheckConstraint)]
        assert len(constraints) >= 2
        
        # Check indexes
        indexes = [arg for arg in table_args if isinstance(arg, Index)]
        assert len(indexes) >= 3
        
        # Check comment dict
        comment_dict = [arg for arg in table_args if isinstance(arg, dict)]
        assert len(comment_dict) == 1
        assert 'comment' in comment_dict[0]

    def test_operation_log_columns(self):
        """Test that OperationLog has all the expected columns with correct types and properties"""
        columns = OperationLog.__table__.columns
        
        # Check log_id column
        assert 'log_id' in columns
        log_id_col = columns['log_id']
        assert isinstance(log_id_col.type, Integer)
        assert log_id_col.primary_key is True
        assert log_id_col.autoincrement is True
        assert log_id_col.comment == '日志ID'

        # Check user_id column
        assert 'user_id' in columns
        user_id_col = columns['user_id']
        assert isinstance(user_id_col.type, Integer)
        assert user_id_col.nullable is False
        assert user_id_col.comment == '操作用户'
        # Check that it has foreign key (without checking specific table)
        assert len(user_id_col.foreign_keys) >= 1

        # Check project_id column
        assert 'project_id' in columns
        project_id_col = columns['project_id']
        assert isinstance(project_id_col.type, Integer)
        assert project_id_col.nullable is False
        assert project_id_col.comment == '所属项目'
        # Check that it has foreign key (without checking specific table)
        assert len(project_id_col.foreign_keys) >= 1

        # Check session_id column
        assert 'session_id' in columns
        session_id_col = columns['session_id']
        assert isinstance(session_id_col.type, Integer)
        assert session_id_col.nullable is False
        assert session_id_col.comment == '所属会话'
        # Check that it has foreign key (without checking specific table)
        assert len(session_id_col.foreign_keys) >= 1

        # Check message_id column
        assert 'message_id' in columns
        message_id_col = columns['message_id']
        assert isinstance(message_id_col.type, Integer)
        assert message_id_col.nullable is False
        assert message_id_col.comment == '触发操作的消息'
        # Check that it has foreign key (without checking specific table)
        assert len(message_id_col.foreign_keys) >= 1

        # Check statement_id column
        assert 'statement_id' in columns
        statement_id_col = columns['statement_id']
        assert isinstance(statement_id_col.type, Integer)
        assert statement_id_col.nullable is False
        assert statement_id_col.comment == '关联的SQL语句'
        # Check that it has foreign key (without checking specific table)
        assert len(statement_id_col.foreign_keys) >= 1

        # Check operation_type column
        assert 'operation_type' in columns
        operation_type_col = columns['operation_type']
        assert isinstance(operation_type_col.type, Text)
        assert operation_type_col.nullable is False
        assert operation_type_col.comment == '操作类型'

        # Check target_table column
        assert 'target_table' in columns
        target_table_col = columns['target_table']
        assert isinstance(target_table_col.type, String)
        assert target_table_col.nullable is False
        assert target_table_col.comment == '目标表名'

        # Check sql_statement column
        assert 'sql_statement' in columns
        sql_statement_col = columns['sql_statement']
        assert isinstance(sql_statement_col.type, Text)
        assert sql_statement_col.nullable is False
        assert sql_statement_col.comment == '完整SQL语句'

        # Check natural_language_intent column
        assert 'natural_language_intent' in columns
        natural_language_intent_col = columns['natural_language_intent']
        assert isinstance(natural_language_intent_col.type, Text)
        assert natural_language_intent_col.nullable is False
        assert natural_language_intent_col.comment == '用户原始指令'

        # Check status column
        assert 'status' in columns
        status_col = columns['status']
        assert isinstance(status_col.type, Text)
        assert status_col.nullable is False
        assert status_col.comment == '执行状态'

        # Check error_message column
        assert 'error_message' in columns
        error_message_col = columns['error_message']
        assert isinstance(error_message_col.type, Text)
        assert error_message_col.nullable is True
        assert error_message_col.comment == '错误信息（若失败）'

        # Check affected_rows column
        assert 'affected_rows' in columns
        affected_rows_col = columns['affected_rows']
        assert isinstance(affected_rows_col.type, Integer)
        assert affected_rows_col.default.arg == 0
        assert affected_rows_col.comment == '影响行数'

        # Check confirmed_by_user column
        assert 'confirmed_by_user' in columns
        confirmed_by_user_col = columns['confirmed_by_user']
        assert isinstance(confirmed_by_user_col.type, Boolean)
        assert confirmed_by_user_col.default.arg is False
        assert confirmed_by_user_col.comment == '是否经用户确认'

        # Check executed_at column
        assert 'executed_at' in columns
        executed_at_col = columns['executed_at']
        assert isinstance(executed_at_col.type, DateTime)
        assert executed_at_col.server_default is not None
        assert executed_at_col.comment == '执行时间'

        # Check execution_duration_ms column
        assert 'execution_duration_ms' in columns
        execution_duration_ms_col = columns['execution_duration_ms']
        assert isinstance(execution_duration_ms_col.type, Integer)
        assert execution_duration_ms_col.comment == '执行耗时（毫秒）'

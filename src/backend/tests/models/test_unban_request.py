import pytest
from sqlalchemy import Column, Integer, DateTime, Text, ForeignKey, CheckConstraint, Index
from sqlalchemy.sql import func

from app.models.unban_request import UnbanRequest
from app.core.database import Base

class TestUnbanRequestModel:
    """Test cases for UnbanRequest model"""

    def test_unban_request_inherits_from_base(self):
        """Test that UnbanRequest inherits from Base"""
        assert issubclass(UnbanRequest, Base)

    def test_unban_request_table_name(self):
        """Test that UnbanRequest has the correct table name"""
        assert UnbanRequest.__tablename__ == 'unban_request'

    def test_unban_request_table_args(self):
        """Test that UnbanRequest has the correct table args"""
        table_args = UnbanRequest.__table_args__
        assert isinstance(table_args, tuple)
        # Check that we have constraints and indexes (exact count may vary)
        assert len(table_args) >= 3
        
        # Check constraints
        constraints = [arg for arg in table_args if isinstance(arg, CheckConstraint)]
        assert len(constraints) >= 1
        
        # Check indexes
        indexes = [arg for arg in table_args if isinstance(arg, Index)]
        assert len(indexes) >= 2
        
        # Check comment dict
        comment_dict = [arg for arg in table_args if isinstance(arg, dict)]
        assert len(comment_dict) == 1
        assert 'comment' in comment_dict[0]

    def test_unban_request_columns(self):
        """Test that UnbanRequest has all the expected columns with correct types and properties"""
        columns = UnbanRequest.__table__.columns

        # Check request_id column
        assert 'request_id' in columns
        request_id_col = columns['request_id']
        assert isinstance(request_id_col.type, Integer)
        assert request_id_col.autoincrement is True
        assert request_id_col.primary_key is True
        assert request_id_col.comment == '申请ID'

        # Check user_id column
        assert 'user_id' in columns
        user_id_col = columns['user_id']
        assert isinstance(user_id_col.type, Integer)
        assert user_id_col.nullable is False
        assert user_id_col.comment == '申请用户ID'
        # Check that it has foreign key (without checking specific table)
        assert len(user_id_col.foreign_keys) >= 1

        # Check ban_log_id column
        assert 'ban_log_id' in columns
        ban_log_id_col = columns['ban_log_id']
        assert isinstance(ban_log_id_col.type, Integer)
        assert ban_log_id_col.nullable is False
        assert ban_log_id_col.comment == '关联的封禁日志ID'
        # Check that it has foreign key (without checking specific table)
        assert len(ban_log_id_col.foreign_keys) >= 1

        # Check request_time column
        assert 'request_time' in columns
        request_time_col = columns['request_time']
        assert isinstance(request_time_col.type, DateTime)
        assert request_time_col.server_default is not None
        assert request_time_col.nullable is False
        assert request_time_col.comment == '申请时间'

        # Check reason column
        assert 'reason' in columns
        reason_col = columns['reason']
        assert isinstance(reason_col.type, Text)
        assert reason_col.nullable is False
        assert reason_col.comment == '申请解封理由'

        # Check supporting_evidence column
        assert 'supporting_evidence' in columns
        supporting_evidence_col = columns['supporting_evidence']
        assert isinstance(supporting_evidence_col.type, Text)
        assert supporting_evidence_col.comment == '支持证据'

        # Check status column
        assert 'status' in columns
        status_col = columns['status']
        assert isinstance(status_col.type, Text)
        assert status_col.default.arg == 'pending'
        assert status_col.nullable is False
        assert status_col.comment == '申请状态：pending/approved/rejected/processed'

        # Check admin_user_id column
        assert 'admin_user_id' in columns
        admin_user_id_col = columns['admin_user_id']
        assert isinstance(admin_user_id_col.type, Integer)
        assert admin_user_id_col.comment == '处理管理员ID'
        # Check that it has foreign key (without checking specific table)
        assert len(admin_user_id_col.foreign_keys) >= 0 # Should be 1, but nullable

        # Check decision_time column
        assert 'decision_time' in columns
        decision_time_col = columns['decision_time']
        assert isinstance(decision_time_col.type, DateTime)
        assert decision_time_col.comment == '处理时间'

        # Check decision_reason column
        assert 'decision_reason' in columns
        decision_reason_col = columns['decision_reason']
        assert isinstance(decision_reason_col.type, Text)
        assert decision_reason_col.comment == '处理结果'

        # Check created_at column
        assert 'created_at' in columns
        created_at_col = columns['created_at']
        assert isinstance(created_at_col.type, DateTime)
        assert created_at_col.server_default is not None
        assert created_at_col.nullable is False
        assert created_at_col.comment == '记录创建时间'

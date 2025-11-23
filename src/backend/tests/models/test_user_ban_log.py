import pytest
from sqlalchemy import Column, Integer, Text, CheckConstraint, DateTime, ForeignKey, Index
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import INTERVAL

from app.models.user_ban_log import UserBanLog
from app.core.database import Base

class TestUserBanLogModel:
    """Test cases for UserBanLog model"""

    def test_user_ban_log_inherits_from_base(self):
        """Test that UserBanLog inherits from Base"""
        assert issubclass(UserBanLog, Base)

    def test_user_ban_log_table_name(self):
        """Test that UserBanLog has the correct table name"""
        assert UserBanLog.__tablename__ == 'user_ban_log'

    def test_user_ban_log_table_args(self):
        """Test that UserBanLog has the correct table args"""
        table_args = UserBanLog.__table_args__
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

    def test_user_ban_log_columns(self):
        """Test that UserBanLog has all the expected columns with correct types and properties"""
        columns = UserBanLog.__table__.columns

        # Check log_id column
        assert 'log_id' in columns
        log_id_col = columns['log_id']
        assert isinstance(log_id_col.type, Integer)
        assert log_id_col.autoincrement is True
        assert log_id_col.primary_key is True
        assert log_id_col.comment == "日志ID"

        # Check target_user_id column
        assert 'target_user_id' in columns
        target_user_id_col = columns['target_user_id']
        assert isinstance(target_user_id_col.type, Integer)
        assert target_user_id_col.nullable is False
        assert target_user_id_col.comment == "被封禁的用户ID"
        # Check that it has foreign key (without checking specific table)
        assert len(target_user_id_col.foreign_keys) >= 1

        # Check admin_user_id column
        assert 'admin_user_id' in columns
        admin_user_id_col = columns['admin_user_id']
        assert isinstance(admin_user_id_col.type, Integer)
        assert admin_user_id_col.nullable is False
        assert admin_user_id_col.comment == "执行操作的管理员ID"
        # Check that it has foreign key (without checking specific table)
        assert len(admin_user_id_col.foreign_keys) >= 1

        # Check action_type column
        assert 'action_type' in columns
        action_type_col = columns['action_type']
        assert isinstance(action_type_col.type, Text)
        assert action_type_col.nullable is False
        assert action_type_col.comment == "操作类型：ban/unban/warning"

        # Check reason column
        assert 'reason' in columns
        reason_col = columns['reason']
        assert isinstance(reason_col.type, Text)
        assert reason_col.nullable is False
        assert reason_col.comment == "封禁/解封原因"

        # Check duration column
        assert 'duration' in columns
        duration_col = columns['duration']
        assert isinstance(duration_col.type, INTERVAL)
        assert duration_col.nullable is True
        assert duration_col.comment == "封禁持续时间"

        # Check effective_time column
        assert 'effective_time' in columns
        effective_time_col = columns['effective_time']
        assert isinstance(effective_time_col.type, DateTime)
        assert effective_time_col.server_default is not None
        assert effective_time_col.nullable is False
        assert effective_time_col.comment == "生效时间"

        # Check expiry_time column
        assert 'expiry_time' in columns
        expiry_time_col = columns['expiry_time']
        assert isinstance(expiry_time_col.type, DateTime)
        assert expiry_time_col.nullable is True
        assert expiry_time_col.comment == "过期时间"

        # Check created_at column
        assert 'created_at' in columns
        created_at_col = columns['created_at']
        assert isinstance(created_at_col.type, DateTime)
        assert created_at_col.server_default is not None
        assert created_at_col.nullable is False
        assert created_at_col.comment == "记录创建时间"

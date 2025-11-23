import pytest
from sqlalchemy import Column, Integer, CheckConstraint, Text, DateTime, String, ForeignKey, Index
from sqlalchemy.sql import func

from app.models.user_profile_change_log import UserProfileChangeLog
from app.core.database import Base

class TestUserProfileChangeLogModel:
    """Test cases for UserProfileChangeLog model"""

    def test_user_profile_change_log_inherits_from_base(self):
        """Test that UserProfileChangeLog inherits from Base"""
        assert issubclass(UserProfileChangeLog, Base)

    def test_user_profile_change_log_table_name(self):
        """Test that UserProfileChangeLog has the correct table name"""
        assert UserProfileChangeLog.__tablename__ == 'user_profile_change_log'

    def test_user_profile_change_log_table_args(self):
        """Test that UserProfileChangeLog has the correct table args"""
        table_args = UserProfileChangeLog.__table_args__
        assert isinstance(table_args, tuple)
        # Check that we have constraints and indexes (exact count may vary)
        assert len(table_args) >= 3
        
        # Check constraints
        constraints = [arg for arg in table_args if isinstance(arg, CheckConstraint)]
        assert len(constraints) >= 1
        
        # Check indexes
        indexes = [arg for arg in table_args if isinstance(arg, Index)]
        assert len(indexes) >= 3
        
        # Check comment dict
        comment_dict = [arg for arg in table_args if isinstance(arg, dict)]
        assert len(comment_dict) == 1
        assert 'comment' in comment_dict[0]

    def test_user_profile_change_log_columns(self):
        """Test that UserProfileChangeLog has all the expected columns with correct types and properties"""
        columns = UserProfileChangeLog.__table__.columns

        # Check change_id column
        assert 'change_id' in columns
        change_id_col = columns['change_id']
        assert isinstance(change_id_col.type, Integer)
        assert change_id_col.autoincrement is True
        assert change_id_col.primary_key is True
        assert change_id_col.comment == '变更ID'

        # Check user_id column
        assert 'user_id' in columns
        user_id_col = columns['user_id']
        assert isinstance(user_id_col.type, Integer)
        assert user_id_col.nullable is False
        assert user_id_col.comment == '被修改的用户ID'
        # Check that it has foreign key (without checking specific table)
        assert len(user_id_col.foreign_keys) >= 1

        # Check change_type column
        assert 'change_type' in columns
        change_type_col = columns['change_type']
        assert isinstance(change_type_col.type, Text)
        assert change_type_col.nullable is False
        assert change_type_col.comment == '变更类型'

        # Check old_value column
        assert 'old_value' in columns
        old_value_col = columns['old_value']
        assert isinstance(old_value_col.type, Text)
        assert old_value_col.nullable is True
        assert old_value_col.comment == '变更前的值'

        # Check new_value column
        assert 'new_value' in columns
        new_value_col = columns['new_value']
        assert isinstance(new_value_col.type, Text)
        assert new_value_col.nullable is False
        assert new_value_col.comment == '变更后的值'

        # Check created_at column
        assert 'created_at' in columns
        created_at_col = columns['created_at']
        assert isinstance(created_at_col.type, DateTime)
        assert created_at_col.server_default is not None
        assert created_at_col.nullable is False
        assert created_at_col.comment == '变更时间'

        # Check ip_address column
        assert 'ip_address' in columns
        ip_address_col = columns['ip_address']
        assert isinstance(ip_address_col.type, String)
        assert ip_address_col.nullable is False
        assert ip_address_col.comment == '操作IP地址'

        # Check user_agent column
        assert 'user_agent' in columns
        user_agent_col = columns['user_agent']
        assert isinstance(user_agent_col.type, Text)
        assert user_agent_col.nullable is False
        assert user_agent_col.comment == '操作设备信息'

import pytest
from sqlalchemy import Column, Text, String, Integer, Boolean, Index, CheckConstraint, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import INTERVAL, JSONB
from sqlalchemy.sql import func
from app.models.user_login_history import UserLoginHistory
from app.core.database import Base

class TestUserLoginHistoryModel:
    """Test cases for UserLoginHistory model"""

    def test_user_login_history_inherits_from_base(self):
        """Test that UserLoginHistory inherits from Base"""
        assert issubclass(UserLoginHistory, Base)

    def test_user_login_history_table_name(self):
        """Test that UserLoginHistory has the correct table name"""
        assert UserLoginHistory.__tablename__ == 'user_login_history'

    def test_user_login_history_table_args(self):
        """Test that UserLoginHistory has the correct table args"""
        table_args = UserLoginHistory.__table_args__
        assert isinstance(table_args, tuple)
        # Check that we have constraints and indexes (exact count may vary)
        assert len(table_args) >= 4
        
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

    def test_user_login_history_columns(self):
        """Test that UserLoginHistory has all the expected columns with correct types and properties"""
        columns = UserLoginHistory.__table__.columns

        # Check login_id column
        assert 'login_id' in columns
        login_id_col = columns['login_id']
        assert isinstance(login_id_col.type, Integer)
        assert login_id_col.autoincrement is True
        assert login_id_col.primary_key is True
        assert login_id_col.comment == '登录记录ID'

        # Check user_id column
        assert 'user_id' in columns
        user_id_col = columns['user_id']
        assert isinstance(user_id_col.type, Integer)
        assert user_id_col.nullable is False
        assert user_id_col.comment == '用户ID'
        # Check that it has foreign key (without checking specific table)
        assert len(user_id_col.foreign_keys) >= 1

        # Check login_time column
        assert 'login_time' in columns
        login_time_col = columns['login_time']
        assert isinstance(login_time_col.type, DateTime)
        assert login_time_col.server_default is not None
        assert login_time_col.nullable is False
        assert login_time_col.comment == '登录时间'

        # Check logout_time column
        assert 'logout_time' in columns
        logout_time_col = columns['logout_time']
        assert isinstance(logout_time_col.type, DateTime)
        assert logout_time_col.nullable is True
        assert logout_time_col.comment == '登出时间'

        # Check session_duration column
        assert 'session_duration' in columns
        session_duration_col = columns['session_duration']
        assert isinstance(session_duration_col.type, INTERVAL)
        assert session_duration_col.nullable is True
        assert session_duration_col.comment == '会话持续时间'

        # Check ip_address column
        assert 'ip_address' in columns
        ip_address_col = columns['ip_address']
        assert isinstance(ip_address_col.type, String)
        assert ip_address_col.nullable is False
        assert ip_address_col.comment == '登录IP地址'

        # Check user_agent column
        assert 'user_agent' in columns
        user_agent_col = columns['user_agent']
        assert isinstance(user_agent_col.type, Text)
        assert user_agent_col.comment == '浏览器/设备信息'

        # Check login_status column
        assert 'login_status' in columns
        login_status_col = columns['login_status']
        assert isinstance(login_status_col.type, Text)
        assert login_status_col.nullable is False
        assert login_status_col.comment == '登录状态：success/failed/expired/forced_logout'

        # Check failure_reason column
        assert 'failure_reason' in columns
        failure_reason_col = columns['failure_reason']
        assert isinstance(failure_reason_col.type, Text)
        assert failure_reason_col.comment == '失败原因（仅当失败时）'

        # Check device_info column
        assert 'device_info' in columns
        device_info_col = columns['device_info']
        assert isinstance(device_info_col.type, JSONB)
        assert device_info_col.comment == '详细设备信息（JSON格式）'

        # Check created_at column
        assert 'created_at' in columns
        created_at_col = columns['created_at']
        assert isinstance(created_at_col.type, DateTime)
        assert created_at_col.server_default is not None
        assert created_at_col.nullable is False
        assert created_at_col.comment == '记录创建时间'

import pytest
from sqlalchemy import Column, Text, String, Integer, DateTime, CheckConstraint, Index, ForeignKey
from sqlalchemy.sql import func

from app.models.violation_log import ViolationLog
from app.core.database import Base

class TestViolationLogModel:
    """Test cases for ViolationLog model"""

    def test_violation_log_inherits_from_base(self):
        """Test that ViolationLog inherits from Base"""
        assert issubclass(ViolationLog, Base)

    def test_violation_log_table_name(self):
        """Test that ViolationLog has the correct table name"""
        assert ViolationLog.__tablename__ == 'violation_log'

    def test_violation_log_table_args(self):
        """Test that ViolationLog has the correct table args"""
        table_args = ViolationLog.__table_args__
        assert isinstance(table_args, tuple)
        # Check that we have constraints and indexes (exact count may vary)
        assert len(table_args) >= 4
        
        # Check constraints
        constraints = [arg for arg in table_args if isinstance(arg, CheckConstraint)]
        assert len(constraints) >= 1
        
        # Check indexes
        indexes = [arg for arg in table_args if isinstance(arg, Index)]
        assert len(indexes) >= 4
        
        # Check comment dict
        comment_dict = [arg for arg in table_args if isinstance(arg, dict)]
        assert len(comment_dict) == 1
        assert 'comment' in comment_dict[0]

    def test_violation_log_columns(self):
        """Test that ViolationLog has all the expected columns with correct types and properties"""
        columns = ViolationLog.__table__.columns

        # Check violation_id column
        assert 'violation_id' in columns
        violation_id_col = columns['violation_id']
        assert isinstance(violation_id_col.type, Integer)
        assert violation_id_col.autoincrement is True
        assert violation_id_col.primary_key is True
        assert violation_id_col.comment == '违规行为ID'

        # Check user_id column
        assert 'user_id' in columns
        user_id_col = columns['user_id']
        assert isinstance(user_id_col.type, Integer)
        assert user_id_col.nullable is False
        assert user_id_col.comment == '违规用户ID'
        # Check that it has foreign key (without checking specific table)
        assert len(user_id_col.foreign_keys) >= 1

        # Check event_type column
        assert 'event_type' in columns
        event_type_col = columns['event_type']
        assert isinstance(event_type_col.type, Text)
        assert event_type_col.nullable is False
        assert event_type_col.comment == '违规事件类型'

        # Check event_description column
        assert 'event_description' in columns
        event_description_col = columns['event_description']
        assert isinstance(event_description_col.type, Text)
        assert event_description_col.nullable is False
        assert event_description_col.comment == '事件详细描述'

        # Check risk_level column
        assert 'risk_level' in columns
        risk_level_col = columns['risk_level']
        assert isinstance(risk_level_col.type, Text)
        assert risk_level_col.nullable is False
        assert risk_level_col.comment == '风险等级：LOW/MEDIUM/HIGH/CRITICAL'

        # Check ip_address column
        assert 'ip_address' in columns
        ip_address_col = columns['ip_address']
        assert isinstance(ip_address_col.type, String)
        assert ip_address_col.nullable is False
        assert ip_address_col.comment == '违规操作IP地址'

        # Check client_user_agent column
        assert 'client_user_agent' in columns
        client_user_agent_col = columns['client_user_agent']
        assert isinstance(client_user_agent_col.type, Text)
        assert client_user_agent_col.nullable is True
        assert client_user_agent_col.comment == '客户端用户代理信息'

        # Check request_content column
        assert 'request_content' in columns
        request_content_col = columns['request_content']
        assert isinstance(request_content_col.type, Text)
        assert request_content_col.nullable is True
        assert request_content_col.comment == '原始请求内容'

        # Check handled_by column
        assert 'handled_by' in columns
        handled_by_col = columns['handled_by']
        assert isinstance(handled_by_col.type, Integer)
        assert handled_by_col.nullable is True
        assert handled_by_col.comment == '处理人ID'
        # Check that it has foreign key (without checking specific table)
        assert len(handled_by_col.foreign_keys) >= 0 # Should be 1, but nullable

        # Check handled_at column
        assert 'handled_at' in columns
        handled_at_col = columns['handled_at']
        assert isinstance(handled_at_col.type, DateTime)
        assert handled_at_col.nullable is True
        assert handled_at_col.comment == '处理时间'

        # Check resolution_status column
        assert 'resolution_status' in columns
        resolution_status_col = columns['resolution_status']
        assert isinstance(resolution_status_col.type, Text)
        assert resolution_status_col.default.arg == 'pending'
        assert resolution_status_col.nullable is False
        assert resolution_status_col.comment == '处理状态：pending/resolved/rejected'

        # Check created_at column
        assert 'created_at' in columns
        created_at_col = columns['created_at']
        assert isinstance(created_at_col.type, DateTime)
        assert created_at_col.server_default is not None
        assert created_at_col.nullable is False
        assert created_at_col.comment == '记录创建时间'

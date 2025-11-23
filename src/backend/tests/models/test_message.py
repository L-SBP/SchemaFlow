import pytest
from sqlalchemy import Column, Integer, Text, Boolean, CheckConstraint, Index, DateTime, ForeignKey

from app.models.message import Message
from app.core.database import Base


class TestMessageModel:
    """Test cases for Message model"""

    def test_message_inherits_from_base(self):
        """Test that Message inherits from Base"""
        assert issubclass(Message, Base)

    def test_message_table_name(self):
        """Test that Message has the correct table name"""
        assert Message.__tablename__ == 'message'

    def test_message_table_args(self):
        """Test that Message has the correct table args"""
        table_args = Message.__table_args__
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

    def test_message_columns(self):
        """Test that Message has all the expected columns with correct types and properties"""
        columns = Message.__table__.columns
        
        # Check message_id column
        assert 'message_id' in columns
        message_id_col = columns['message_id']
        assert isinstance(message_id_col.type, Integer)
        assert message_id_col.primary_key is True
        assert message_id_col.autoincrement is True
        assert message_id_col.comment == '消息ID'

        # Check session_id column
        assert 'session_id' in columns
        session_id_col = columns['session_id']
        assert isinstance(session_id_col.type, Integer)
        assert session_id_col.nullable is False
        assert session_id_col.comment == '所属会话'
        # Check that it has foreign key (without checking specific table)
        assert len(session_id_col.foreign_keys) >= 1

        # Check message_type column
        assert 'message_type' in columns
        message_type_col = columns['message_type']
        assert isinstance(message_type_col.type, Text)
        assert message_type_col.nullable is False
        assert message_type_col.comment == '消息类型：user/assistant/system'

        # Check content column
        assert 'content' in columns
        content_col = columns['content']
        assert isinstance(content_col.type, Text)
        assert content_col.nullable is False
        assert content_col.comment == '原始文本内容'

        # Check requires_confirmation column
        assert 'requires_confirmation' in columns
        requires_confirmation_col = columns['requires_confirmation']
        assert isinstance(requires_confirmation_col.type, Boolean)
        assert requires_confirmation_col.default.arg is False
        assert requires_confirmation_col.comment == '是否需要用户确认'

        # Check user_confirmed column
        assert 'user_confirmed' in columns
        user_confirmed_col = columns['user_confirmed']
        assert isinstance(user_confirmed_col.type, Boolean)
        assert user_confirmed_col.default.arg is False
        assert user_confirmed_col.comment == '用户是否确认执行'

        # Check created_at column
        assert 'created_at' in columns
        created_at_col = columns['created_at']
        assert isinstance(created_at_col.type, DateTime)
        assert created_at_col.server_default is not None
        assert created_at_col.comment == '创建时间'
import pytest
from sqlalchemy import Column, String, CheckConstraint, Index, Integer, ForeignKey, DateTime
from sqlalchemy.sql import func
from app.models.session import Session
from app.core.database import Base

class TestSessionModel:
    """Test cases for Session model"""

    def test_session_inherits_from_base(self):
        """Test that Session inherits from Base"""
        assert issubclass(Session, Base)

    def test_session_table_name(self):
        """Test that Session has the correct table name"""
        assert Session.__tablename__ == 'session'

    def test_session_table_args(self):
        """Test that Session has the correct table args"""
        table_args = Session.__table_args__
        assert isinstance(table_args, tuple)
        # Check that we have indexes (exact count may vary)
        assert len(table_args) >= 2
        
        # Check indexes
        indexes = [arg for arg in table_args if isinstance(arg, Index)]
        assert len(indexes) >= 2
        
        # Check comment dict
        comment_dict = [arg for arg in table_args if isinstance(arg, dict)]
        assert len(comment_dict) == 1
        assert 'comment' in comment_dict[0]

    def test_session_columns(self):
        """Test that Session has all the expected columns with correct types and properties"""
        columns = Session.__table__.columns

        # Check session_id column
        assert 'session_id' in columns
        session_id_col = columns['session_id']
        assert isinstance(session_id_col.type, Integer)
        assert session_id_col.autoincrement is True
        assert session_id_col.primary_key is True
        assert session_id_col.comment == '会话ID'

        # Check project_id column
        assert 'project_id' in columns
        project_id_col = columns['project_id']
        assert isinstance(project_id_col.type, Integer)
        assert project_id_col.nullable is False
        assert project_id_col.comment == '关联的项目ID'
        # Check that it has foreign key (without checking specific table)
        assert len(project_id_col.foreign_keys) >= 1

        # Check session_name column
        assert 'session_name' in columns
        session_name_col = columns['session_name']
        assert isinstance(session_name_col.type, String)
        assert session_name_col.nullable is False
        assert session_name_col.default.arg == 'New Session'
        assert session_name_col.comment == '会话名称'

        # Check created_at column
        assert 'created_at' in columns
        created_at_col = columns['created_at']
        assert isinstance(created_at_col.type, DateTime)
        assert created_at_col.server_default is not None
        assert created_at_col.comment == '创建时间'

        # Check last_activity column
        assert 'last_activity' in columns
        last_activity_col = columns['last_activity']
        assert isinstance(last_activity_col.type, DateTime)
        assert last_activity_col.server_default is not None
        assert last_activity_col.onupdate is not None
        assert last_activity_col.nullable is True
        assert last_activity_col.comment == '最后活动时间'

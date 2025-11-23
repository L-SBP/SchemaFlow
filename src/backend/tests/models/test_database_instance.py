import pytest
from sqlalchemy import Column, Integer, String, Text, DateTime, CheckConstraint, Index
from sqlalchemy.sql import func

from app.models.database_instance import DatabaseInstance
from app.core.database import Base


class TestDatabaseInstanceModel:
    """Test cases for DatabaseInstance model"""

    def test_database_instance_inherits_from_base(self):
        """Test that DatabaseInstance inherits from Base"""
        assert issubclass(DatabaseInstance, Base)

    def test_database_instance_table_name(self):
        """Test that DatabaseInstance has the correct table name"""
        assert DatabaseInstance.__tablename__ == 'database_instance'

    def test_database_instance_table_args(self):
        """Test that DatabaseInstance has the correct table args"""
        table_args = DatabaseInstance.__table_args__
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

    def test_database_instance_columns(self):
        """Test that DatabaseInstance has all the expected columns with correct types and properties"""
        columns = DatabaseInstance.__table__.columns
        
        # Check instance_id column
        assert 'instance_id' in columns
        instance_id_col = columns['instance_id']
        assert isinstance(instance_id_col.type, Integer)
        assert instance_id_col.primary_key is True
        assert instance_id_col.autoincrement is True
        assert instance_id_col.comment == '实例ID'

        # Check db_type column
        assert 'db_type' in columns
        db_type_col = columns['db_type']
        assert isinstance(db_type_col.type, Text)
        assert db_type_col.nullable is False
        assert db_type_col.default.arg == 'mysql'
        assert db_type_col.comment == '数据库类型'

        # Check db_host column
        assert 'db_host' in columns
        db_host_col = columns['db_host']
        assert isinstance(db_host_col.type, String)
        assert db_host_col.nullable is False
        assert db_host_col.comment == '数据库主机地址'

        # Check db_port column
        assert 'db_port' in columns
        db_port_col = columns['db_port']
        assert isinstance(db_port_col.type, Integer)
        assert db_port_col.default.arg == 3306
        assert db_port_col.comment == '端口'

        # Check db_name column
        assert 'db_name' in columns
        db_name_col = columns['db_name']
        assert isinstance(db_name_col.type, String)
        assert db_name_col.nullable is False
        assert db_name_col.comment == '数据库名'

        # Check db_username column
        assert 'db_username' in columns
        db_username_col = columns['db_username']
        assert isinstance(db_username_col.type, String)
        assert db_username_col.nullable is False
        assert db_username_col.comment == '用户名'

        # Check db_password column
        assert 'db_password' in columns
        db_password_col = columns['db_password']
        assert isinstance(db_password_col.type, String)
        assert db_password_col.nullable is False
        assert db_password_col.comment == '密码（加密存储）'

        # Check status column
        assert 'status' in columns
        status_col = columns['status']
        assert isinstance(status_col.type, Text)
        assert status_col.default.arg == 'active'
        assert status_col.nullable is False
        assert status_col.comment == '实例状态'

        # Check created_at column
        assert 'created_at' in columns
        created_at_col = columns['created_at']
        assert isinstance(created_at_col.type, DateTime)
        assert created_at_col.server_default is not None
        assert created_at_col.comment == '创建时间'

        # Check last_used_at column
        assert 'last_used_at' in columns
        last_used_at_col = columns['last_used_at']
        assert isinstance(last_used_at_col.type, DateTime)
        assert last_used_at_col.server_default is not None
        assert last_used_at_col.onupdate is not None
        assert last_used_at_col.nullable is True
        assert last_used_at_col.comment == '最后使用时间'

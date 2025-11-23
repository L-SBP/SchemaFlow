import pytest
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, CheckConstraint, Index
from sqlalchemy.sql import func

from app.models.user_account import UserAccount
from app.core.database import Base


class TestUserAccountModel:
    """Test cases for UserAccount model"""

    def test_user_account_inherits_from_base(self):
        """Test that UserAccount inherits from Base"""
        assert issubclass(UserAccount, Base)

    def test_user_account_table_name(self):
        """Test that UserAccount has the correct table name"""
        assert UserAccount.__tablename__ == 'user_account'

    def test_user_account_table_args(self):
        """Test that UserAccount has the correct table args"""
        table_args = UserAccount.__table_args__
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

    def test_user_account_columns(self):
        """Test that UserAccount has all the expected columns with correct types and properties"""
        columns = UserAccount.__table__.columns
        
        # Check user_id column
        assert 'user_id' in columns
        user_id_col = columns['user_id']
        assert isinstance(user_id_col.type, Integer)
        assert user_id_col.primary_key is True
        assert user_id_col.autoincrement is True
        assert user_id_col.index is True
        assert user_id_col.comment == '用户唯一ID'

        # Check username column
        assert 'username' in columns
        username_col = columns['username']
        assert isinstance(username_col.type, String)
        assert username_col.unique is True
        assert username_col.index is True
        assert username_col.nullable is False
        assert username_col.comment == '用户名'

        # Check email column
        assert 'email' in columns
        email_col = columns['email']
        assert isinstance(email_col.type, String)
        assert email_col.unique is True
        assert email_col.index is True
        assert email_col.nullable is False
        assert email_col.comment == '注册邮箱'

        # Check password_hash column
        assert 'password_hash' in columns
        password_hash_col = columns['password_hash']
        assert isinstance(password_hash_col.type, String)
        assert password_hash_col.nullable is False
        assert password_hash_col.comment == '加密后的密码'

        # Check status column
        assert 'status' in columns
        status_col = columns['status']
        assert isinstance(status_col.type, Text)
        assert status_col.default.arg == 'normal'
        assert status_col.nullable is False
        assert status_col.comment == '账户状态：normal/suspended/banned'

        # Check used_databases column
        assert 'used_databases' in columns
        used_databases_col = columns['used_databases']
        assert isinstance(used_databases_col.type, Integer)
        assert used_databases_col.default.arg == 0
        assert used_databases_col.nullable is False
        assert used_databases_col.comment == '已使用的数据库项目数'

        # Check avatar_url column
        assert 'avatar_url' in columns
        avatar_url_col = columns['avatar_url']
        assert isinstance(avatar_url_col.type, Text)
        assert avatar_url_col.comment == '头像图片URL'

        # Check is_admin column
        assert 'is_admin' in columns
        is_admin_col = columns['is_admin']
        assert isinstance(is_admin_col.type, Boolean)
        assert is_admin_col.default.arg is False
        assert is_admin_col.comment == '是否为管理员'

        # Check max_databases column
        assert 'max_databases' in columns
        max_databases_col = columns['max_databases']
        assert isinstance(max_databases_col.type, Integer)
        assert max_databases_col.default.arg == 10
        assert max_databases_col.comment == '允许创建的最大数据库项目数'

        # Check last_login_at column
        assert 'last_login_at' in columns
        last_login_at_col = columns['last_login_at']
        assert isinstance(last_login_at_col.type, DateTime)
        assert last_login_at_col.server_default is not None
        assert last_login_at_col.comment == '最后登录时间'

        # Check created_at column
        assert 'created_at' in columns
        created_at_col = columns['created_at']
        assert isinstance(created_at_col.type, DateTime)
        assert created_at_col.server_default is not None
        assert created_at_col.comment == '注册时间'
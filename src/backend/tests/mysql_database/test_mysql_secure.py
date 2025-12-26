import pytest
from unittest.mock import patch

from app.mysql.mysql_secure import normalize_sql, match_operation, validate_safe_sql
from app.core.exceptions import SQLSecurityException


class TestMysqlSecure:
    """Test cases for mysql_secure.py"""

    def test_normalize_sql(self):
        """Test SQL normalization function"""
        # Test removing comments
        sql_with_comment = "SELECT * FROM users -- This is a comment"
        assert normalize_sql(sql_with_comment) == "SELECT * FROM USERS"

        # Test removing extra spaces and newlines
        sql_with_spaces = "SELECT   *   \nFROM\tusers"
        assert normalize_sql(sql_with_spaces) == "SELECT * FROM USERS"

        # Test uppercase conversion
        sql_lowercase = "select * from users"
        assert normalize_sql(sql_lowercase) == "SELECT * FROM USERS"

    def test_match_operation(self):
        """Test SQL operation matching"""
        # Test exact match
        assert match_operation("CREATE DATABASE test", ["CREATE DATABASE *"]) is True

        # Test wildcard match
        assert match_operation("CREATE DATABASE mydb", ["CREATE DATABASE *"]) is True

        # Test no match
        assert match_operation("DROP TABLE users", ["CREATE DATABASE *"]) is False

        # Test case insensitive match
        assert match_operation("create database test", ["CREATE DATABASE *"]) is True

        # Test return False when no patterns match
        assert match_operation("SELECT * FROM users", []) is False

    @patch('app.mysql.mysql_secure.config')
    def test_validate_safe_sql_root_allowed(self, mock_config):
        """Test SQL validation for root user with allowed operation"""
        # Setup mock config
        mock_config.sql_permissions.root.allowed_operations = ["CREATE DATABASE *"]
        mock_config.sql_permissions.root.forbidden_operations = ["DROP DATABASE *"]

        # Should not raise exception for allowed operation
        try:
            validate_safe_sql("CREATE DATABASE test", is_root=True)
        except SQLSecurityException:
            pytest.fail("validate_safe_sql raised SQLSecurityException unexpectedly")

    @patch('app.mysql.mysql_secure.config')
    def test_validate_safe_sql_root_forbidden(self, mock_config):
        """Test SQL validation for root user with forbidden operation"""
        # Setup mock config
        mock_config.sql_permissions.root.allowed_operations = ["CREATE DATABASE *"]
        mock_config.sql_permissions.root.forbidden_operations = ["DROP DATABASE *"]

        # Should raise exception for forbidden operation
        with pytest.raises(SQLSecurityException):
            validate_safe_sql("DROP DATABASE test", is_root=True)

    @patch('app.mysql.mysql_secure.config')
    def test_validate_safe_sql_user_allowed(self, mock_config):
        """Test SQL validation for normal user with allowed operation"""
        # Setup mock config
        mock_config.sql_permissions.normal.allowed_operations = ["SELECT *"]
        mock_config.sql_permissions.normal.forbidden_operations = ["CREATE *", "DROP *", "ALTER *"]

        # Should not raise exception for allowed operation
        try:
            validate_safe_sql("SELECT * FROM users", is_root=False)
        except SQLSecurityException:
            pytest.fail("validate_safe_sql raised SQLSecurityException unexpectedly")

    @patch('app.mysql.mysql_secure.config')
    def test_validate_safe_sql_user_not_allowed(self, mock_config):
        """Test SQL validation for normal user with not allowed operation"""
        # Setup mock config
        mock_config.sql_permissions.normal.allowed_operations = ["SELECT *"]
        mock_config.sql_permissions.normal.forbidden_operations = ["CREATE *", "DROP *", "ALTER *"]

        # Should raise exception for operation not in allowed list
        with pytest.raises(SQLSecurityException):
            validate_safe_sql("INSERT INTO users VALUES (1, 'John')", is_root=False)
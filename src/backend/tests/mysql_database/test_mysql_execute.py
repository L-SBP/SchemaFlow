import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from app.mysql.mysql_execute import execute_sql_root, execute_dql_user, execute_dml_user
from app.core.exceptions import SQLSecurityException


class TestMysqlExecute:
    """Test cases for mysql_execute.py"""

    @patch('app.mysql.mysql_execute.validate_safe_sql')
    @patch('app.mysql.mysql_execute.MysqlHelper')
    @pytest.mark.asyncio
    async def test_execute_sql_root(self, mock_mysql_helper, mock_validate_safe_sql):
        """Test executing SQL as root user"""
        # Setup mocks
        mock_engine = MagicMock()
        mock_connection = AsyncMock()
        mock_connection.__aenter__ = AsyncMock(return_value=mock_connection)
        mock_connection.__aexit__ = AsyncMock()
        mock_engine.connect = MagicMock(return_value=mock_connection)
        mock_mysql_helper.get_root_engine = AsyncMock(return_value=mock_engine)
        mock_connection.execute = AsyncMock()

        sql = "CREATE DATABASE test_db"

        # Run the method
        await execute_sql_root(sql)

        # Assertions
        mock_validate_safe_sql.assert_called_once_with(sql, is_root=True)
        mock_mysql_helper.get_root_engine.assert_called_once()
        mock_engine.connect.assert_called_once()
        mock_connection.execute.assert_called_once()

    @patch('app.mysql.mysql_execute.validate_safe_sql')
    @patch('app.mysql.mysql_execute.MysqlHelper')
    @patch('app.mysql.mysql_execute.DatabaseInstance')
    @pytest.mark.asyncio
    async def test_execute_dql_user(self, mock_database_instance, mock_mysql_helper, mock_validate_safe_sql):
        """Test executing DQL as user"""
        # Setup mocks
        mock_engine = MagicMock()
        mock_connection = AsyncMock()
        mock_result = MagicMock()
        
        mock_connection.__aenter__ = AsyncMock(return_value=mock_connection)
        mock_connection.__aexit__ = AsyncMock()
        mock_engine.connect = MagicMock(return_value=mock_connection)
        mock_connection.execute = AsyncMock(return_value=mock_result)
        mock_result.mappings = MagicMock()
        mock_result.mappings().fetchall = MagicMock(return_value=[
            {"id": 1, "name": "John"},
            {"id": 2, "name": "Jane"}
        ])
        mock_mysql_helper.get_user_engine = AsyncMock(return_value=mock_engine)

        dql = "SELECT * FROM users"
        mock_instance = MagicMock()

        # Run the method
        result = await execute_dql_user(dql, mock_instance)

        # Assertions
        mock_validate_safe_sql.assert_called_once_with(dql, is_root=False)
        mock_mysql_helper.get_user_engine.assert_called_once_with(mock_instance)
        mock_engine.connect.assert_called_once()
        mock_connection.execute.assert_called_once()
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["id"] == 1
        assert result[0]["name"] == "John"

    @patch('app.mysql.mysql_execute.validate_safe_sql')
    @patch('app.mysql.mysql_execute.MysqlHelper')
    @patch('app.mysql.mysql_execute.DatabaseInstance')
    @pytest.mark.asyncio
    async def test_execute_dml_user(self, mock_database_instance, mock_mysql_helper, mock_validate_safe_sql):
        """Test executing DML as user"""
        # Setup mocks
        mock_engine = MagicMock()
        mock_connection = AsyncMock()
        mock_result = MagicMock()
        
        mock_connection.__aenter__ = AsyncMock(return_value=mock_connection)
        mock_connection.__aexit__ = AsyncMock()
        mock_engine.connect = MagicMock(return_value=mock_connection)
        mock_connection.execute = AsyncMock(return_value=mock_result)
        mock_connection.commit = AsyncMock()
        
        mock_result.rowcount = 1
        mock_result.lastrowid = 10
        mock_mysql_helper.get_user_engine = AsyncMock(return_value=mock_engine)

        dml = "INSERT INTO users (name) VALUES ('John')"
        mock_instance = MagicMock()

        # Run the method
        result = await execute_dml_user(dml, mock_instance)

        # Assertions
        mock_validate_safe_sql.assert_called_once_with(dml, is_root=False)
        mock_mysql_helper.get_user_engine.assert_called_once_with(mock_instance)
        mock_engine.connect.assert_called_once()
        mock_connection.execute.assert_called_once()
        mock_connection.commit.assert_called_once()
        assert isinstance(result, dict)
        assert result["rowcount"] == 1
        assert result["lastrowid"] == 10

    @patch('app.mysql.mysql_execute.validate_safe_sql')
    @pytest.mark.asyncio
    async def test_execute_sql_root_security_exception(self, mock_validate_safe_sql):
        """Test executing SQL as root with security violation"""
        # Setup mock to raise exception
        mock_validate_safe_sql.side_effect = SQLSecurityException("Operation not allowed")
        
        sql = "DROP DATABASE test_db"

        # Run the method and check exception
        with pytest.raises(SQLSecurityException):
            await execute_sql_root(sql)

        # Assertions
        mock_validate_safe_sql.assert_called_once_with(sql, is_root=True)
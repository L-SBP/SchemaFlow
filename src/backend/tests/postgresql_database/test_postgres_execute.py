import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from src.backend.app.postgresql.postgres_execute import (
    execute_sql_root, 
    execute_dql_root, 
    execute_dql_user, 
    execute_dml_user,
    deploy_postgres_ddl
)
from src.backend.app.core.exceptions import SQLSecurityException, DatabaseOperationFailedException


class TestPostgresExecute:
    """Test cases for postgres_execute.py"""

    @patch('app.postgresql.postgres_execute.validate_safe_sql')
    @patch('app.postgresql.postgres_execute.PostgresHelper')
    @pytest.mark.asyncio
    async def test_execute_sql_root(self, mock_postgres_helper, mock_validate_safe_sql):
        """Test executing SQL as root user"""
        # Setup mocks
        mock_engine = MagicMock()
        mock_connection = AsyncMock()
        mock_connection.__aenter__ = AsyncMock(return_value=mock_connection)
        mock_connection.__aexit__ = AsyncMock()
        mock_engine.connect = MagicMock(return_value=mock_connection)
        mock_postgres_helper.get_root_engine = AsyncMock(return_value=mock_engine)
        mock_connection.execute = AsyncMock()

        sql = "CREATE DATABASE test_db"

        # Run the method
        await execute_sql_root(sql)

        # Assertions
        mock_validate_safe_sql.assert_called_once_with(sql, is_root=True)
        mock_postgres_helper.get_root_engine.assert_called_once()
        mock_engine.connect.assert_called_once()
        mock_connection.execute.assert_called_once()

    @patch('app.postgresql.postgres_execute.PostgresHelper')
    @pytest.mark.asyncio
    async def test_execute_dql_root(self, mock_postgres_helper):
        """Test executing DQL as root user"""
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
        mock_postgres_helper.get_root_engine = AsyncMock(return_value=mock_engine)

        dql = "SELECT * FROM users"

        # Run the method
        result = await execute_dql_root(dql)

        # Assertions
        mock_postgres_helper.get_root_engine.assert_called_once()
        mock_engine.connect.assert_called_once()
        mock_connection.execute.assert_called_once()
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["id"] == 1
        assert result[0]["name"] == "John"

    @patch('app.postgresql.postgres_execute.validate_safe_sql')
    @patch('app.postgresql.postgres_execute.PostgresHelper')
    @patch('app.postgresql.postgres_execute.DatabaseInstance')
    @pytest.mark.asyncio
    async def test_execute_dql_user(self, mock_database_instance, mock_postgres_helper, mock_validate_safe_sql):
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
        mock_postgres_helper.get_user_engine = AsyncMock(return_value=mock_engine)

        dql = "SELECT * FROM users"
        mock_instance = MagicMock()

        # Run the method
        result = await execute_dql_user(dql, mock_instance)

        # Assertions
        mock_validate_safe_sql.assert_called_once_with(dql, is_root=False)
        mock_postgres_helper.get_user_engine.assert_called_once_with(mock_instance)
        mock_engine.connect.assert_called_once()
        mock_connection.execute.assert_called_once()
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["id"] == 1
        assert result[0]["name"] == "John"

    @patch('app.postgresql.postgres_execute.validate_safe_sql')
    @patch('app.postgresql.postgres_execute.PostgresHelper')
    @patch('app.postgresql.postgres_execute.DatabaseInstance')
    @pytest.mark.asyncio
    async def test_execute_dml_user(self, mock_database_instance, mock_postgres_helper, mock_validate_safe_sql):
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
        mock_postgres_helper.get_user_engine = AsyncMock(return_value=mock_engine)

        dml = "INSERT INTO users (name) VALUES ('John')"
        mock_instance = MagicMock()

        # Run the method
        result = await execute_dml_user(dml, mock_instance)

        # Assertions
        mock_validate_safe_sql.assert_called_once_with(dml, is_root=False)
        mock_postgres_helper.get_user_engine.assert_called_once_with(mock_instance)
        mock_engine.connect.assert_called_once()
        mock_connection.execute.assert_called_once()
        mock_connection.commit.assert_called_once()
        assert isinstance(result, dict)
        assert result["rowcount"] == 1
        assert result["lastrowid"] == 10

    @patch('app.postgresql.postgres_execute.validate_safe_sql')
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

    @patch('app.postgresql.postgres_execute.PostgresHelper')
    @patch('app.postgresql.postgres_execute.create_async_engine')
    @pytest.mark.asyncio
    async def test_deploy_postgres_ddl(self, mock_create_async_engine, mock_postgres_helper):
        """Test deploying PostgreSQL DDL"""
        # Setup mocks
        mock_root_engine = MagicMock()
        mock_root_engine.url = MagicMock()
        mock_root_engine.url.set = MagicMock(return_value="postgresql://test_db")
        mock_postgres_helper.get_root_engine = AsyncMock(return_value=mock_root_engine)
        
        mock_temp_engine = MagicMock()
        mock_temp_conn = AsyncMock()
        mock_temp_conn.__aenter__ = AsyncMock(return_value=mock_temp_conn)
        mock_temp_conn.__aexit__ = AsyncMock()
        mock_temp_engine.connect = MagicMock(return_value=mock_temp_conn)
        mock_temp_engine.dispose = AsyncMock()
        mock_create_async_engine.side_effect = [mock_temp_engine, MagicMock()]
        
        mock_db_engine = MagicMock()
        mock_db_conn = AsyncMock()
        mock_db_conn.__aenter__ = AsyncMock(return_value=mock_db_conn)
        mock_db_conn.__aexit__ = AsyncMock()
        mock_db_conn.commit = AsyncMock()
        mock_db_engine.connect = MagicMock(return_value=mock_db_conn)
        mock_db_engine.dispose = AsyncMock()
        
        # Override second call to create_async_engine
        def side_effect(*args, **kwargs):
            if mock_create_async_engine.call_count == 2:
                return mock_db_engine
            return mock_temp_engine
        
        mock_create_async_engine.side_effect = side_effect

        statements = [
            "CREATE TABLE users (id SERIAL PRIMARY KEY, name VARCHAR(50))",
            "INSERT INTO users (name) VALUES ('John')"
        ]

        # Run the method
        await deploy_postgres_ddl("test_db", statements)

        # Assertions
        assert mock_create_async_engine.call_count == 2
        mock_postgres_helper.get_root_engine.assert_called_once()
        assert mock_temp_engine.dispose.call_count == 1

    @patch('app.postgresql.postgres_execute.PostgresHelper')
    @patch('app.postgresql.postgres_execute.create_async_engine')
    @pytest.mark.asyncio
    async def test_deploy_postgres_ddl_exception(self, mock_create_async_engine, mock_postgres_helper):
        """Test deploying PostgreSQL DDL with exception"""
        # Setup mocks to raise exception
        mock_postgres_helper.get_root_engine = AsyncMock(side_effect=Exception("Connection failed"))

        statements = ["CREATE TABLE users (id SERIAL PRIMARY KEY, name VARCHAR(50))"]

        # Run the method and check exception
        with pytest.raises(DatabaseOperationFailedException):
            await deploy_postgres_ddl("test_db", statements)
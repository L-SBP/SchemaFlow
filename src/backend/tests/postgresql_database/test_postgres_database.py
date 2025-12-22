# 然后直接导入
from postgresql.postgres_database import PostgresHelper
from core.exceptions import InvalidOperationException

import pytest
from unittest.mock import patch, MagicMock, AsyncMock

class TestPostgresDatabase:
    """Test cases for postgres_database.py"""

    @patch('postgresql.postgres_database.create_async_engine')
    @patch('postgresql.postgres_database.PostgresConfig')
    @pytest.mark.asyncio
    async def test_init_root_engine(self, mock_postgres_config, mock_create_engine):
        """Test initializing root engine"""
        # Setup mocks
        mock_engine = AsyncMock()
        mock_create_engine.return_value = mock_engine
        mock_config = MagicMock()
        mock_config.sqlalchemy_database_url = "postgresql+asyncpg://postgres:password@localhost:3245"
        mock_config.pool_size = 2
        mock_config.pool_recycle = 3600
        mock_config.pool_timeout = 30
        mock_config.max_overflow = 0

        # Run the method
        await PostgresHelper.init_root_engine(mock_config)

        # Assertions
        mock_create_engine.assert_called_once_with(
            mock_config.sqlalchemy_database_url,
            connect_args={},
            pool_size=mock_config.pool_size,
            pool_recycle=mock_config.pool_recycle,
            pool_timeout=mock_config.pool_timeout,
            max_overflow=mock_config.max_overflow
        )
        assert PostgresHelper._root_engine == mock_engine

    @patch('postgresql.postgres_database.create_async_engine')
    @patch('postgresql.postgres_database.PostgresConfig')
    @patch('postgresql.postgres_database.DatabaseInstance')
    @pytest.mark.asyncio
    async def test_init_user_engine(self, mock_database_instance, mock_postgres_config, mock_create_engine):
        """Test initializing user engine"""
        # Setup mocks
        mock_engine = AsyncMock()
        mock_create_engine.return_value = mock_engine
        mock_config = MagicMock()
        mock_config.pool_size = 5
        mock_config.pool_recycle = 3600
        mock_config.pool_timeout = 30
        mock_config.max_overflow = 10

        mock_instance = MagicMock()
        mock_instance.instance_id = 1
        mock_instance.user_database_url = "postgresql+asyncpg://user:password@localhost:5432/db"

        # Run the method
        await PostgresHelper.init_user_engine(mock_config, mock_instance.instance_id, mock_instance.user_database_url)

        # Assertions
        mock_create_engine.assert_called_once_with(
            mock_instance.user_database_url,
            connect_args={},
            pool_size=mock_config.pool_size,
            pool_recycle=mock_config.pool_recycle,
            pool_timeout=mock_config.pool_timeout,
            max_overflow=mock_config.max_overflow
        )
        assert PostgresHelper._user_engine[mock_instance.instance_id] == mock_engine

    @pytest.mark.asyncio
    async def test_get_root_engine_success(self):
        """Test getting root engine when initialized"""
        # Setup
        mock_engine = AsyncMock()
        PostgresHelper._root_engine = mock_engine

        # Run the method
        result = await PostgresHelper.get_root_engine()

        # Assertions
        assert result == mock_engine

    @pytest.mark.asyncio
    async def test_get_root_engine_failure(self):
        """Test getting root engine when not initialized"""
        # Setup
        PostgresHelper._root_engine = None

        # Run the method and check exception
        with pytest.raises(InvalidOperationException):
            await PostgresHelper.get_root_engine()

    @patch('postgresql.postgres_database.DatabaseInstance')
    @pytest.mark.asyncio
    async def test_get_user_engine_success(self, mock_database_instance):
        """Test getting user engine when initialized"""
        # Setup
        mock_engine = AsyncMock()
        mock_instance = MagicMock()
        mock_instance.instance_id = 1
        PostgresHelper._user_engine = {mock_instance.instance_id: mock_engine}

        # Run the method
        result = await PostgresHelper.get_user_engine(mock_instance)

        # Assertions
        assert result == mock_engine

    @patch('postgresql.postgres_database.DatabaseInstance')
    @pytest.mark.asyncio
    async def test_get_user_engine_failure(self, mock_database_instance):
        """Test getting user engine when not initialized"""
        # Setup
        mock_instance = MagicMock()
        mock_instance.instance_id = 1
        PostgresHelper._user_engine = {}

        # Run the method and check exception
        with pytest.raises(InvalidOperationException):
            await PostgresHelper.get_user_engine(mock_instance)

    @pytest.mark.asyncio
    async def test_close_root_engine(self):
        """Test closing root engine"""
        # Setup
        mock_engine = AsyncMock()
        mock_engine.dispose = AsyncMock()
        PostgresHelper._root_engine = mock_engine

        # Run the method
        await PostgresHelper.close_root_engine()

        # Assertions
        mock_engine.dispose.assert_called_once()
        assert PostgresHelper._root_engine is None

    @pytest.mark.asyncio
    @patch('postgresql.postgres_database.DatabaseInstance')
    async def test_close_user_engine(self, mock_database_instance):
        """Test closing user engine"""
        # Setup
        mock_engine = AsyncMock()
        mock_engine.dispose = AsyncMock()
        mock_instance = MagicMock()
        mock_instance.instance_id = 1
        PostgresHelper._user_engine = {mock_instance.instance_id: mock_engine}

        # Run the method
        await PostgresHelper.close_user_engine(mock_instance)

        # Assertions
        mock_engine.dispose.assert_called_once()
        assert mock_instance.instance_id not in PostgresHelper._user_engine

    @pytest.mark.asyncio
    async def test_close_all_engine(self):
        """Test closing all engines"""
        # Setup
        mock_root_engine = AsyncMock()
        mock_root_engine.dispose = AsyncMock()
        PostgresHelper._root_engine = mock_root_engine

        mock_user_engine = AsyncMock()
        mock_user_engine.dispose = AsyncMock()
        PostgresHelper._user_engine = {1: mock_user_engine}

        # Run the method
        await PostgresHelper.close_all_engine()

        # Assertions
        mock_root_engine.dispose.assert_called_once()
        mock_user_engine.dispose.assert_called_once()
        assert PostgresHelper._root_engine is None

    def test_is_user_engine_exists(self):
        """Test checking if user engine exists"""
        # Setup
        PostgresHelper._user_engine = {1: MagicMock(), 2: MagicMock()}

        # Test existing engine
        assert PostgresHelper.is_user_engine_exists(1) is True

        # Test non-existing engine
        assert PostgresHelper.is_user_engine_exists(3) is False

    def test_is_user_exists(self):
        """Test checking if user exists in local cache"""
        # Setup
        PostgresHelper._user_exist = {"user1", "user2"}

        # Test existing user
        assert PostgresHelper.is_user_exists("user1") is True

        # Test non-existing user
        assert PostgresHelper.is_user_exists("user3") is False

    def test_add_user(self):
        """Test adding user to local cache"""
        # Setup
        PostgresHelper._user_exist = set()
        PostgresHelper._root_engine = MagicMock()

        # Run the method
        PostgresHelper.add_user("new_user")

        # Assertions
        assert "new_user" in PostgresHelper._user_exist

    @patch('postgresql.postgres_database.PostgresHelper.get_root_engine')
    @pytest.mark.asyncio
    async def test_is_user_exist_in_postgres(self, mock_get_root_engine):
        """Test checking if user exists in PostgreSQL"""
        # Setup
        mock_engine = MagicMock()
        mock_connection = AsyncMock()
        mock_result = MagicMock()

        mock_connection.__aenter__ = AsyncMock(return_value=mock_connection)
        mock_connection.__aexit__ = AsyncMock()
        mock_engine.connect = MagicMock(return_value=mock_connection)
        mock_connection.execute = AsyncMock(return_value=mock_result)
        mock_result.fetchone = MagicMock(return_value=MagicMock())
        mock_get_root_engine.return_value = mock_engine

        PostgresHelper._root_engine = mock_engine

        # Run the method
        result = await PostgresHelper.is_user_exist_in_postgres("test_user")

        # Assertions
        assert result is True
        mock_get_root_engine.assert_called_once()
        mock_engine.connect.assert_called_once()
        mock_connection.execute.assert_called_once()

    @patch('postgresql.postgres_database.PostgresHelper.get_root_engine')
    @pytest.mark.asyncio
    async def test_is_user_exist_in_postgres_no_user(self, mock_get_root_engine):
        """Test checking if user exists in PostgreSQL when user doesn't exist"""
        # Setup
        mock_engine = MagicMock()
        mock_connection = AsyncMock()
        mock_result = MagicMock()

        mock_connection.__aenter__ = AsyncMock(return_value=mock_connection)
        mock_connection.__aexit__ = AsyncMock()
        mock_engine.connect = MagicMock(return_value=mock_connection)
        mock_connection.execute = AsyncMock(return_value=mock_result)
        mock_result.fetchone = MagicMock(return_value=None)
        mock_get_root_engine.return_value = mock_engine

        PostgresHelper._root_engine = mock_engine

        # Run the method
        result = await PostgresHelper.is_user_exist_in_postgres("test_user")

        # Assertions
        assert result is False
        mock_get_root_engine.assert_called_once()
        mock_engine.connect.assert_called_once()
        mock_connection.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_is_user_exist_in_postgres_no_root_engine(self):
        """Test checking if user exists in PostgreSQL when root engine is not initialized"""
        # Setup
        PostgresHelper._root_engine = None

        # Run the method and check exception
        with pytest.raises(InvalidOperationException):
            await PostgresHelper.is_user_exist_in_postgres("test_user")

    @patch('postgresql.postgres_database.PostgresHelper.get_root_engine')
    @pytest.mark.asyncio
    async def test_check_privilege(self, mock_get_root_engine):
        """Test checking user privileges"""
        # Setup
        mock_engine = MagicMock()
        mock_connection = AsyncMock()
        mock_result = MagicMock()

        mock_connection.__aenter__ = AsyncMock(return_value=mock_connection)
        mock_connection.__aexit__ = AsyncMock()
        mock_engine.connect = MagicMock(return_value=mock_connection)
        mock_connection.execute = AsyncMock(return_value=mock_result)
        mock_result.fetchall = MagicMock(return_value=[
            MagicMock(privilege_type="SELECT"),
            MagicMock(privilege_type="INSERT"),
            MagicMock(privilege_type="UPDATE"),
            MagicMock(privilege_type="DELETE")
        ])
        mock_get_root_engine.return_value = mock_engine

        PostgresHelper._root_engine = mock_engine

        # Run the method
        result = await PostgresHelper.check_privilege("test_user", "test_db")

        # Assertions
        assert result is True
        mock_get_root_engine.assert_called_once()
        mock_engine.connect.assert_called_once()
        mock_connection.execute.assert_called_once()

    @patch('postgresql.postgres_database.PostgresHelper.get_root_engine')
    @pytest.mark.asyncio
    async def test_check_privilege_insufficient_privileges(self, mock_get_root_engine):
        """Test checking user privileges when user has insufficient privileges"""
        # Setup
        mock_engine = MagicMock()
        mock_connection = AsyncMock()
        mock_result = MagicMock()

        mock_connection.__aenter__ = AsyncMock(return_value=mock_connection)
        mock_connection.__aexit__ = AsyncMock()
        mock_engine.connect = MagicMock(return_value=mock_connection)
        mock_connection.execute = AsyncMock(return_value=mock_result)
        mock_result.fetchall = MagicMock(return_value=[
            MagicMock(privilege_type="SELECT")
        ])
        mock_get_root_engine.return_value = mock_engine

        PostgresHelper._root_engine = mock_engine

        # Run the method
        result = await PostgresHelper.check_privilege("test_user", "test_db")

        # Assertions
        assert result is False
        mock_get_root_engine.assert_called_once()
        mock_engine.connect.assert_called_once()
        mock_connection.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_privilege_no_root_engine(self):
        """Test checking user privileges when root engine is not initialized"""
        # Setup
        PostgresHelper._root_engine = None

        # Run the method and check exception
        with pytest.raises(InvalidOperationException):
            await PostgresHelper.check_privilege("test_user", "test_db")

    @patch('app.postgresql.postgres_database.PostgresHelper.get_root_engine')
    @pytest.mark.asyncio
    async def test_grant_user_privileges(self, mock_get_root_engine):
        """Test granting user privileges"""
        # Setup
        mock_engine = MagicMock()
        mock_connection = AsyncMock()

        mock_connection.__aenter__ = AsyncMock(return_value=mock_connection)
        mock_connection.__aexit__ = AsyncMock()
        mock_engine.connect = MagicMock(return_value=mock_connection)
        mock_connection.execute = AsyncMock()
        mock_get_root_engine.return_value = mock_engine

        PostgresHelper._root_engine = mock_engine

        # Run the method
        await PostgresHelper.grant_user_privileges("test_db", "test_user")

        # Assertions
        mock_get_root_engine.assert_called_once()
        mock_engine.connect.assert_called_once()
        assert mock_connection.execute.call_count == 5  # 5 GRANT/ALTER statements

    @pytest.mark.asyncio
    async def test_grant_user_privileges_no_root_engine(self):
        """Test granting user privileges when root engine is not initialized"""
        # Setup
        PostgresHelper._root_engine = None

        # Run the method and check exception
        with pytest.raises(InvalidOperationException):
            await PostgresHelper.grant_user_privileges("test_db", "test_user")
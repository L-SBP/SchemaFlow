import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from app.mysql.mysql_database import MysqlHelper
from app.core.exceptions import InvalidOperationException


class TestMysqlDatabase:
    """Test cases for mysql_database.py"""

    @patch('app.mysql.mysql_database.create_async_engine')
    @patch('app.mysql.mysql_database.MySQLConfig')
    @pytest.mark.asyncio
    async def test_init_root_engine(self, mock_mysql_config, mock_create_engine):
        """Test initializing root engine"""
        # Setup mocks
        mock_engine = AsyncMock()
        mock_create_engine.return_value = mock_engine
        mock_config = MagicMock()
        mock_config.plugin = "mysql_native_password"
        mock_config.ssl = False
        mock_config.sqlalchemy_database_url = "mysql+aiomysql://root:password@localhost:3306"
        mock_config.pool_size = 2
        mock_config.pool_recycle = 3600
        mock_config.pool_timeout = 30
        mock_config.max_overflow = 0

        # Run the method
        await MysqlHelper.init_root_engine(mock_config)

        # Assertions
        mock_create_engine.assert_called_once_with(
            mock_config.sqlalchemy_database_url,
            connect_args={
                "auth_plugin": mock_config.plugin,
                "ssl": mock_config.ssl
            },
            pool_size=mock_config.pool_size,
            pool_recycle=mock_config.pool_recycle,
            pool_timeout=mock_config.pool_timeout,
            max_overflow=mock_config.max_overflow
        )
        assert MysqlHelper._root_engine == mock_engine

    @patch('app.mysql.mysql_database.create_async_engine')
    @patch('app.mysql.mysql_database.MySQLConfig')
    @patch('app.mysql.mysql_database.DatabaseInstance')
    @pytest.mark.asyncio
    async def test_init_user_engine(self, mock_database_instance, mock_mysql_config, mock_create_engine):
        """Test initializing user engine"""
        # Setup mocks
        mock_engine = AsyncMock()
        mock_create_engine.return_value = mock_engine
        mock_config = MagicMock()
        mock_config.plugin = "mysql_native_password"
        mock_config.ssl = False
        mock_config.pool_size = 5
        mock_config.pool_recycle = 3600
        mock_config.pool_timeout = 30
        mock_config.max_overflow = 10

        mock_instance = MagicMock()
        mock_instance.instance_id = 1
        mock_instance.user_database_url = "mysql+aiomysql://user:password@localhost:3306/db"

        # Run the method
        await MysqlHelper.init_user_engine(mock_config, mock_instance)

        # Assertions
        mock_create_engine.assert_called_once_with(
            mock_instance.user_database_url,
            connect_args={
                "auth_plugin": mock_config.plugin,
                "ssl": mock_config.ssl
            },
            pool_size=mock_config.pool_size,
            pool_recycle=mock_config.pool_recycle,
            pool_timeout=mock_config.pool_timeout,
            max_overflow=mock_config.max_overflow
        )
        assert MysqlHelper._user_engine[mock_instance.instance_id] == mock_engine

    @pytest.mark.asyncio
    async def test_get_root_engine_success(self):
        """Test getting root engine when initialized"""
        # Setup
        mock_engine = AsyncMock()
        MysqlHelper._root_engine = mock_engine

        # Run the method
        result = await MysqlHelper.get_root_engine()

        # Assertions
        assert result == mock_engine

    @pytest.mark.asyncio
    async def test_get_root_engine_failure(self):
        """Test getting root engine when not initialized"""
        # Setup
        MysqlHelper._root_engine = None

        # Run the method and check exception
        with pytest.raises(InvalidOperationException):
            await MysqlHelper.get_root_engine()

    @patch('app.mysql.mysql_database.DatabaseInstance')
    @pytest.mark.asyncio
    async def test_get_user_engine_success(self, mock_database_instance):
        """Test getting user engine when initialized"""
        # Setup
        mock_engine = AsyncMock()
        mock_instance = MagicMock()
        mock_instance.instance_id = 1
        MysqlHelper._user_engine = {mock_instance.instance_id: mock_engine}

        # Run the method
        result = await MysqlHelper.get_user_engine(mock_instance)

        # Assertions
        assert result == mock_engine

    @patch('app.mysql.mysql_database.DatabaseInstance')
    @pytest.mark.asyncio
    async def test_get_user_engine_failure(self, mock_database_instance):
        """Test getting user engine when not initialized"""
        # Setup
        mock_instance = MagicMock()
        mock_instance.instance_id = 1
        MysqlHelper._user_engine = {}

        # Run the method and check exception
        with pytest.raises(InvalidOperationException):
            await MysqlHelper.get_user_engine(mock_instance)

    @pytest.mark.asyncio
    async def test_close_root_engine(self):
        """Test closing root engine"""
        # Setup
        mock_engine = AsyncMock()
        mock_engine.dispose = AsyncMock()
        MysqlHelper._root_engine = mock_engine

        # Run the method
        await MysqlHelper.close_root_engine()

        # Assertions
        mock_engine.dispose.assert_called_once()
        assert MysqlHelper._root_engine is None

    @pytest.mark.asyncio
    @patch('app.mysql.mysql_database.DatabaseInstance')
    async def test_close_user_engine(self, mock_database_instance):
        """Test closing user engine"""
        # Setup
        mock_engine = AsyncMock()
        mock_engine.dispose = AsyncMock()
        mock_instance = MagicMock()
        mock_instance.instance_id = 1
        MysqlHelper._user_engine = {mock_instance.instance_id: mock_engine}

        # Run the method
        await MysqlHelper.close_user_engine(mock_instance)

        # Assertions
        mock_engine.dispose.assert_called_once()
        assert mock_instance.instance_id not in MysqlHelper._user_engine

    @pytest.mark.asyncio
    async def test_close_all_engine(self):
        """Test closing all engines"""
        # Setup
        mock_root_engine = AsyncMock()
        mock_root_engine.dispose = AsyncMock()
        MysqlHelper._root_engine = mock_root_engine

        mock_user_engine = AsyncMock()
        mock_user_engine.dispose = AsyncMock()
        MysqlHelper._user_engine = {1: mock_user_engine}

        # Run the method
        await MysqlHelper.close_all_engine()

        # Assertions
        mock_root_engine.dispose.assert_called_once()
        mock_user_engine.dispose.assert_called_once()
        assert MysqlHelper._root_engine is None
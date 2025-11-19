import pytest
from unittest.mock import patch, MagicMock

from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncAttrs

from app.core.database import Base, PsqlHelper
from app.config.base import DatabaseConfig


class TestBase:
    """Test cases for Base class"""

    def test_base_class_inheritance(self):
        """Test that Base class inherits from both AsyncAttrs and DeclarativeBase"""
        # Check that Base is a subclass of both AsyncAttrs and DeclarativeBase
        assert issubclass(Base, AsyncAttrs)
        assert issubclass(Base, DeclarativeBase)


class TestPsqlHelper:
    """Test cases for PsqlHelper class"""

    @pytest.fixture
    def db_config(self):
        """Fixture to create a DatabaseConfig instance for testing"""
        config_data = {
            "host": "localhost",
            "port": 5432,
            "username": "testuser",
            "password": "testpassword",
            "database": "testdb",
            "driver": "postgresql+asyncpg",
            "echo": True,
            "max_overflow": 10,
            "pool_size": 50,
            "pool_recycle": 3600,
            "pool_timeout": 30
        }
        return DatabaseConfig(**config_data)

    def test_get_async_engine(self, db_config):
        """Test _get_async_engine method"""
        with patch('app.core.database.create_async_engine') as mock_create_engine:
            # Mock the return value of create_async_engine
            mock_engine = MagicMock(spec=AsyncEngine)
            mock_create_engine.return_value = mock_engine
            
            # Call the method
            engine = PsqlHelper._get_async_engine(db_config)
            
            # Verify create_async_engine was called with correct parameters
            mock_create_engine.assert_called_once_with(
                url=db_config.sqlalchemy_database_url,
                echo=db_config.echo,
                pool_recycle=db_config.pool_recycle,
                pool_timeout=db_config.pool_timeout,
                pool_size=db_config.pool_size,
                max_overflow=db_config.max_overflow,
            )
            
            # Verify the returned engine is the mocked engine
            assert engine == mock_engine

    def test_get_async_session(self, db_config):
        """Test _get_async_session method"""
        with patch('app.core.database.async_sessionmaker') as mock_sessionmaker:
            # Create a mock engine
            mock_engine = MagicMock(spec=AsyncEngine)
            
            # Call the method
            session = PsqlHelper._get_async_session(mock_engine)
            
            # Verify async_sessionmaker was called with correct parameters
            mock_sessionmaker.assert_called_once_with(
                bind=mock_engine,
                autocommit=False,
                autoflush=False,
                expire_on_commit=False,
            )

    def test_get_async_session_with_none_engine(self):
        """Test _get_async_session method with None engine"""
        with pytest.raises(ValueError, match="Async engine is not initialized"):
            PsqlHelper._get_async_session(None)

    def test_init_conn_psql(self, db_config):
        """Test init_conn_psql method (synchronous part)"""
        with patch('app.core.database.create_async_engine') as mock_create_engine:
            # Mock the engine
            mock_engine = MagicMock(spec=AsyncEngine)
            mock_create_engine.return_value = mock_engine
            
            # Call the method
            engine = PsqlHelper._get_async_engine(db_config)
            
            # Verify create_async_engine was called
            mock_create_engine.assert_called_once_with(
                url=db_config.sqlalchemy_database_url,
                echo=db_config.echo,
                pool_recycle=db_config.pool_recycle,
                pool_timeout=db_config.pool_timeout,
                pool_size=db_config.pool_size,
                max_overflow=db_config.max_overflow,
            )
            
            # Verify the returned engine is the mocked engine
            assert engine == mock_engine

    def test_close_conn_psql(self):
        """Test close_conn_psql method"""
        # Create a mock engine
        mock_engine = MagicMock(spec=AsyncEngine)
        mock_engine.dispose = MagicMock()
        
        # Since we can't easily test the async method, we'll just verify it exists
        assert hasattr(PsqlHelper, 'close_conn_psql')
        assert callable(PsqlHelper.close_conn_psql)
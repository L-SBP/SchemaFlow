import pytest
from unittest.mock import patch, MagicMock

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncEngine

from app import server
from app.core.database import PsqlHelper


class TestServer:
    """Test cases for server.py"""

    def test_server_app_creation(self):
        """Test that the FastAPI app is created with correct configuration"""
        # Check that app is an instance of FastAPI
        assert isinstance(server.app, FastAPI)
        
        # Check that app has correct title, description, and version from config
        assert server.app.title == "Auto Database Deployment"
        assert server.app.description == "自然语言创建、操作数据库"
        assert server.app.version == "1.0.0"
        
        # Check that the app has a lifespan context (we can verify this by checking if it's set)
        # The lifespan parameter is used during app initialization, not stored as an attribute

    @pytest.mark.asyncio
    async def test_startup_services(self):
        """Test the startup_services function"""
        # Create a mock FastAPI app
        mock_app = MagicMock(spec=FastAPI)
        mock_app.state = MagicMock()
        
        # Mock PsqlHelper.init_conn_psql to return a mock engine
        mock_engine = MagicMock(spec=AsyncEngine)
        with patch('app.core.database.PsqlHelper.init_conn_psql', return_value=mock_engine):
            # Call startup_services
            await server.startup_services(mock_app)
            
            # Verify that app.state.config is set
            assert hasattr(mock_app.state, 'config')
            assert mock_app.state.config == server.config
            
            # Verify that app.state.psql_engine is set to the mock engine
            assert mock_app.state.psql_engine == mock_engine

    @pytest.mark.asyncio
    async def test_close_services(self):
        """Test the close_services function"""
        # Create a mock FastAPI app
        mock_app = MagicMock(spec=FastAPI)
        mock_app.state = MagicMock()
        
        # Create a mock engine
        mock_engine = MagicMock(spec=AsyncEngine)
        mock_app.state.psql_engine = mock_engine
        
        # Mock PsqlHelper.close_conn_psql
        with patch('app.core.database.PsqlHelper.close_conn_psql') as mock_close_conn:
            # Call close_services
            await server.close_services(mock_app)
            
            # Verify that PsqlHelper.close_conn_psql was called with the mock engine
            mock_close_conn.assert_called_once_with(mock_engine)

    @pytest.mark.asyncio
    async def test_lifespan(self):
        """Test the lifespan context manager"""
        # Create a mock FastAPI app
        mock_app = MagicMock(spec=FastAPI)
        mock_app.state = MagicMock()
        
        # Create a mock engine
        mock_engine = MagicMock(spec=AsyncEngine)
        mock_app.state.psql_engine = mock_engine
        
        # Mock both startup and close services
        with patch('app.core.database.PsqlHelper.init_conn_psql', return_value=mock_engine) as mock_init_conn, \
             patch('app.core.database.PsqlHelper.close_conn_psql') as mock_close_conn:
            
            # Test the lifespan context manager
            async with server.lifespan(mock_app):
                # Verify that startup_services was called
                assert hasattr(mock_app.state, 'config')
                assert mock_app.state.config == server.config
                assert mock_app.state.psql_engine == mock_engine
            
            # Verify that both functions were called
            mock_init_conn.assert_called_once()
            mock_close_conn.assert_called_once_with(mock_engine)
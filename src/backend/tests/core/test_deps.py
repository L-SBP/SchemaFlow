import pytest
from unittest.mock import MagicMock

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncEngine

from app.core.deps import get_engin_from_fastapi


class TestGetEngineFromFastAPI:
    """Test cases for get_engin_from_fastapi function"""

    def test_get_engine_from_fastapi(self):
        """Test get_engin_from_fastapi function"""
        # Create a mock engine
        mock_engine = MagicMock(spec=AsyncEngine)
        
        # Create a mock request with app.state.psql_engine
        mock_request = MagicMock(spec=Request)
        mock_request.app.state.psql_engine = mock_engine
        
        # Call the function
        engine = get_engin_from_fastapi(mock_request)
        
        # Verify the engine is returned correctly
        assert engine == mock_engine
        assert isinstance(engine, AsyncEngine)

    def test_get_engine_from_fastapi_with_none_engine(self):
        """Test get_engin_from_fastapi function with None engine"""
        # Create a mock request with None engine
        mock_request = MagicMock(spec=Request)
        mock_request.app.state.psql_engine = None
        
        # Call the function
        engine = get_engin_from_fastapi(mock_request)
        
        # Verify None is returned
        assert engine is None

    def test_get_engine_from_fastapi_with_missing_state(self):
        """Test get_engin_from_fastapi function with missing app state"""
        # Create a mock request without proper state
        mock_request = MagicMock(spec=Request)
        del mock_request.app.state.psql_engine
        
        # This should raise an AttributeError
        with pytest.raises(AttributeError):
            get_engin_from_fastapi(mock_request)
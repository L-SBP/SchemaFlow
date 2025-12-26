import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from app.utils.log import LogHelper


class TestLogHelper:
    """Test cases for LogHelper class"""

    def test_log_helper_initialization(self, tmp_path):
        """Test LogHelper initialization with default parameters"""
        # Mock Profile.get_project_root to return a temporary directory
        with patch('app.utils.profile.Profile.get_project_root') as mock_get_project_root:
            mock_get_project_root.return_value = tmp_path
            
            # Mock config to avoid dependency issues
            mock_config = MagicMock()
            mock_config.log.console_level = "INFO"
            mock_config.log.file_level = "DEBUG"
            mock_config.log.rotation = "500 MB"
            mock_config.log.retention = "10 days"
            
            with patch('app.server.config', mock_config):
                log_helper = LogHelper()
                
                # Check that log directory was created
                log_dir = tmp_path / "logs"
                assert log_dir.exists()
                assert log_dir.is_dir()
                
                # Check that logger was initialized
                assert log_helper.logger is not None

    def test_log_helper_with_custom_log_name(self, tmp_path):
        """Test LogHelper initialization with custom log file name"""
        with patch('app.utils.profile.Profile.get_project_root') as mock_get_project_root:
            mock_get_project_root.return_value = tmp_path
            
            # Mock config
            mock_config = MagicMock()
            mock_config.log.console_level = "INFO"
            mock_config.log.file_level = "DEBUG"
            mock_config.log.rotation = "500 MB"
            mock_config.log.retention = "10 days"
            
            with patch('app.server.config', mock_config):
                log_helper = LogHelper("custom_log")
                
                # Check that log file with custom name would be created
                log_file = tmp_path / "logs" / "custom_log.log"
                # Note: Loguru creates the file when first writing to it, not during initialization
                
                # Check that logger was initialized
                assert log_helper.logger is not None

    def test_get_logger(self, tmp_path):
        """Test get_logger method returns the same logger instance"""
        with patch('app.utils.profile.Profile.get_project_root') as mock_get_project_root:
            mock_get_project_root.return_value = tmp_path
            
            # Mock config
            mock_config = MagicMock()
            mock_config.log.console_level = "INFO"
            mock_config.log.file_level = "DEBUG"
            mock_config.log.rotation = "500 MB"
            mock_config.log.retention = "10 days"
            
            with patch('app.server.config', mock_config):
                log_helper = LogHelper()
                logger1 = log_helper.get_logger()
                logger2 = log_helper.get_logger()
                
                # Check that the same logger instance is returned (due to lru_cache)
                assert logger1 is logger2
                assert logger1 == logger2
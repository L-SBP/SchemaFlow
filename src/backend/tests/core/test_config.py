import pytest
from unittest.mock import patch, mock_open
import yaml

from app.core.config import get_config
from app.config.base import BaseConfig


class TestGetConfig:
    """Test cases for get_config function"""

    def test_get_config_default(self):
        """Test get_config with default parameters"""
        # Mock the config file content to match the actual config.yaml
        mock_yaml_content = {
            "env": "dev",
            "dev": {
                "app": {
                    "name": "Auto Database Deployment",
                    "description": "自然语言创建、操作数据库",
                    "api": "/api/v1",
                    "host": "0.0.0.0",
                    "port": 8000,
                    "uvicorn": "app.server:app",
                    "version": "1.0.0",
                    "reload": True
                },
                "db": {
                    "host": "localhost",
                    "port": 5432,
                    "username": "admin",
                    "password": "secure_2025",
                    "database": "auto_db_deployment",
                    "driver": "postgresql_database+asyncpg",
                    "echo": True,
                    "max_overflow": 10,
                    "pool_size": 50,
                    "pool_recycle": 3600,
                    "pool_timeout": 30
                },
                "redis_client": {
                    "host": "localhost",
                    "port": 6379,
                    "username": "",
                    "password": "",
                    "db": 0
                },
                "log": {
                    "file_level": "DEBUG",
                    "console_level": "INFO",
                    "retention": "10 days",
                    "rotation": "500 MB"
                }
            }
        }

        with patch('app.utils.profile.Profile.get_project_root') as mock_get_project_root, \
             patch('builtins.open', mock_open(read_data=yaml.dump(mock_yaml_content))) as mock_file:
            
            # Mock project root path
            mock_get_project_root.return_value.joinpath.return_value = "config.yaml"
            
            config = get_config()
            
            # Verify the returned config is a BaseConfig instance
            assert isinstance(config, BaseConfig)
            
            # Verify some key values
            assert config.app.name == "Auto Database Deployment"
            assert config.db.host == "localhost"
            assert config.redis.host == "localhost"
            assert config.log.file_level == "DEBUG"

    def test_get_config_with_custom_env(self):
        """Test get_config with custom environment parameter"""
        mock_yaml_content = {
            "env": "prod",
            "dev": {
                "app": {
                    "name": "Auto Database Deployment",
                    "description": "自然语言创建、操作数据库",
                    "api": "/api/v1",
                    "host": "0.0.0.0",
                    "port": 8000,
                    "uvicorn": "app.server:app",
                    "version": "1.0.0",
                    "reload": True
                },
                "db": {
                    "host": "localhost",
                    "port": 5432,
                    "username": "admin",
                    "password": "secure_2025",
                    "database": "auto_db_deployment",
                    "driver": "postgresql_database+asyncpg",
                    "echo": True,
                    "max_overflow": 10,
                    "pool_size": 50,
                    "pool_recycle": 3600,
                    "pool_timeout": 30
                },
                "redis_client": {
                    "host": "localhost",
                    "port": 6379,
                    "username": "",
                    "password": "",
                    "db": 0
                },
                "log": {
                    "file_level": "DEBUG",
                    "console_level": "INFO",
                    "retention": "10 days",
                    "rotation": "500 MB"
                }
            },
            "prod": {
                "app": {
                    "name": "Auto Database Deployment",
                    "description": "自然语言创建、操作数据库",
                    "api": "/api/v1",
                    "host": "0.0.0.0",
                    "port": 8000,
                    "uvicorn": "app.main:app",
                    "version": "1.0.0",
                    "reload": True
                },
                "db": {
                    "host": "localhost",
                    "port": 5432,
                    "username": "admin",
                    "password": "secure_2025",
                    "database": "auto_db_deployment",
                    "driver": "postgresql_database+asyncpg",
                    "echo": True,
                    "max_overflow": 10,
                    "pool_size": 50,
                    "pool_recycle": 3600,
                    "pool_timeout": 30
                },
                "redis_client": {
                    "host": "localhost",
                    "port": 6379,
                    "username": "",
                    "password": "",
                    "db": 0
                },
                "log": {
                    "file_level": "DEBUG",
                    "console_level": "WARN",
                    "retention": "7 days",
                    "rotation": "1 GB"
                }
            }
        }

        with patch('app.utils.profile.Profile.get_project_root') as mock_get_project_root, \
             patch('builtins.open', mock_open(read_data=yaml.dump(mock_yaml_content))) as mock_file:
            
            # Mock project root path
            mock_get_project_root.return_value.joinpath.return_value = "config.yaml"
            
            # Test with prod environment
            config = get_config(env="prod")
            
            # Verify the returned config is a BaseConfig instance
            assert isinstance(config, BaseConfig)
            
            # Verify prod values
            assert config.app.name == "Auto Database Deployment"
            assert config.app.reload is True
            assert config.db.host == "localhost"
            assert config.db.echo is True
            assert config.redis.host == "localhost"
            assert config.log.console_level == "WARN"
            
            # Test with dev environment
            config = get_config(env="dev")
            
            # Verify dev values
            assert config.app.name == "Auto Database Deployment"
            assert config.app.reload is True
            assert config.db.host == "localhost"
            assert config.db.echo is True
            assert config.redis.host == "localhost"
            assert config.log.console_level == "INFO"

    def test_get_config_lru_cache(self):
        """Test that get_config uses lru_cache correctly"""
        mock_yaml_content = {
            "env": "dev",
            "dev": {
                "app": {
                    "name": "Auto Database Deployment",
                    "description": "自然语言创建、操作数据库",
                    "api": "/api/v1",
                    "host": "0.0.0.0",
                    "port": 8000,
                    "uvicorn": "app.server:app",
                    "version": "1.0.0",
                    "reload": True
                },
                "db": {
                    "host": "localhost",
                    "port": 5432,
                    "username": "admin",
                    "password": "secure_2025",
                    "database": "auto_db_deployment",
                    "driver": "postgresql_database+asyncpg",
                    "echo": True,
                    "max_overflow": 10,
                    "pool_size": 50,
                    "pool_recycle": 3600,
                    "pool_timeout": 30
                },
                "redis_client": {
                    "host": "localhost",
                    "port": 6379,
                    "username": "",
                    "password": "",
                    "db": 0
                },
                "log": {
                    "file_level": "DEBUG",
                    "console_level": "INFO",
                    "retention": "10 days",
                    "rotation": "500 MB"
                }
            }
        }

        with patch('app.utils.profile.Profile.get_project_root') as mock_get_project_root, \
             patch('builtins.open', mock_open(read_data=yaml.dump(mock_yaml_content))) as mock_file:
            
            # Mock project root path
            mock_get_project_root.return_value.joinpath.return_value = "config.yaml"
            
            # Call get_config twice
            config1 = get_config()
            config2 = get_config()
            
            # With lru_cache, both calls should return the same object
            assert config1 is config2
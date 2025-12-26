"""
Test cases for configuration modules
"""
import pytest
from pydantic import SecretStr, ValidationError

from app.config.base import Appconfig, DatabaseConfig, RedisConfig, BaseConfig, LogConfig
from app.core.config import get_config

class TestAppConfig:
    """Test cases for Appconfig class"""

    def test_app_config_creation(self):
        """Test creation of Appconfig with valid data"""
        config_data = {
            "name": "Test App",
            "description": "A test application",
            "api": "/api/v1",
            "host": "0.0.0.0",
            "port": 8000,
            "uvicorn": "app.main:app",
            "version": "1.0.0",
            "reload": True
        }
        
        app_config = Appconfig(**config_data)
        assert app_config.name == "Test App"
        assert app_config.description == "A test application"
        assert app_config.api == "/api/v1"
        assert app_config.host == "0.0.0.0"
        assert app_config.port == 8000
        assert app_config.uvicorn == "app.main:app"
        assert app_config.version == "1.0.0"
        assert app_config.reload is True

    def test_app_config_missing_required_fields(self):
        """Test Appconfig with missing required fields raises ValidationError"""
        incomplete_data = {
            "name": "Test App",
            # Missing other required fields
        }
        
        with pytest.raises(ValidationError):
            Appconfig(**incomplete_data)


class TestDatabaseConfig:
    """Test cases for DatabaseConfig class"""

    def test_database_config_creation(self):
        """Test creation of DatabaseConfig with valid data"""
        config_data = {
            "host": "localhost",
            "port": 5432,
            "username": "testuser",
            "password": "testpassword",
            "database": "testdb",
            "driver": "postgresql_database+asyncpg",
            "echo": True,
            "max_overflow": 10,
            "pool_size": 50,
            "pool_recycle": 3600,
            "pool_timeout": 30
        }
        
        db_config = DatabaseConfig(**config_data)
        assert db_config.host == "localhost"
        assert db_config.port == 5432
        assert db_config.username == "testuser"
        assert isinstance(db_config.password, SecretStr)
        assert db_config.database == "testdb"
        assert db_config.driver == "postgresql_database+asyncpg"
        assert db_config.echo is True
        assert db_config.max_overflow == 10
        assert db_config.pool_size == 50
        assert db_config.pool_recycle == 3600
        assert db_config.pool_timeout == 30

    def test_database_config_sqlalchemy_url(self):
        """Test DatabaseConfig sqlalchemy_database_url property"""
        config_data = {
            "host": "localhost",
            "port": 5432,
            "username": "testuser",
            "password": "testpassword",
            "database": "testdb",
            "driver": "postgresql_database+asyncpg",
            "echo": True,
            "max_overflow": 10,
            "pool_size": 50,
            "pool_recycle": 3600,
            "pool_timeout": 30
        }
        
        db_config = DatabaseConfig(**config_data)
        url = db_config.sqlalchemy_database_url
        assert url.drivername == "postgresql_database+asyncpg"
        assert url.username == "testuser"
        assert url.password == "testpassword"
        assert url.host == "localhost"
        assert url.port == 5432
        assert url.database == "testdb"


class TestRedisConfig:
    """Test cases for RedisConfig class"""

    def test_redis_config_creation(self):
        """Test creation of RedisConfig with valid data"""
        config_data = {
            "host": "localhost",
            "port": 6379,
            "username": "redisuser",
            "password": "redispassword",
            "db": 0
        }
        
        redis_config = RedisConfig(**config_data)
        assert redis_config.host == "localhost"
        assert redis_config.port == 6379
        assert redis_config.username == "redisuser"
        assert redis_config.password == "redispassword"
        assert redis_config.db == 0

    def test_redis_config_optional_fields(self):
        """Test RedisConfig with optional fields"""
        config_data = {
            "host": "localhost",
            "port": 6379,
            "username": "",
            "password": "",
            "db": 0
        }
        
        redis_config = RedisConfig(**config_data)
        assert redis_config.username == ""
        assert redis_config.password == ""


class TestLogConfig:
    """Test cases for LogConfig class"""

    def test_log_config_creation(self):
        """Test creation of LogConfig with valid data"""
        config_data = {
            "file_level": "DEBUG",
            "console_level": "INFO",
            "retention": "10 days",
            "rotation": "500 MB"
        }
        
        log_config = LogConfig(**config_data)
        assert log_config.file_level == "DEBUG"
        assert log_config.console_level == "INFO"
        assert log_config.retention == "10 days"
        assert log_config.rotation == "500 MB"


class TestBaseConfig:
    """Test cases for BaseConfig class"""

    def test_base_config_creation(self):
        """Test creation of BaseConfig with valid data"""
        app_config_data = {
            "name": "Test App",
            "description": "A test application",
            "api": "/api/v1",
            "host": "0.0.0.0",
            "port": 8000,
            "uvicorn": "app.main:app",
            "version": "1.0.0",
            "reload": True
        }
        
        db_config_data = {
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
        
        redis_config_data = {
            "host": "localhost",
            "port": 6379,
            "username": "redisuser",
            "password": "redispassword",
            "db": 0
        }
        
        log_config_data = {
            "file_level": "DEBUG",
            "console_level": "INFO",
            "retention": "10 days",
            "rotation": "500 MB"
        }
        
        config_data = {
            "app": app_config_data,
            "db": db_config_data,
            "redis_client": redis_config_data,
            "log": log_config_data
        }
        
        base_config = BaseConfig(**config_data)
        assert isinstance(base_config.app, Appconfig)
        assert isinstance(base_config.db, DatabaseConfig)
        assert isinstance(base_config.redis, RedisConfig)
        assert isinstance(base_config.log, LogConfig)


class TestGetConfig:
    """Test cases for get_config function"""

    def test_get_config_default(self):
        """Test get_config function with default parameters"""
        config = get_config()
        assert isinstance(config, BaseConfig)
        assert config.app.name == "Auto Database Deployment"
        assert config.db.host == "localhost"
        assert config.redis.host == "localhost"
        assert config.log.file_level == "DEBUG"

    def test_get_config_with_custom_env(self):
        """Test get_config function with custom environment"""
        # Test with dev environment specifically
        config = get_config("config.yaml", "dev")
        assert isinstance(config, BaseConfig)
        assert config.app.name == "Auto Database Deployment"
        assert config.db.host == "localhost"
        assert config.redis.host == "localhost"
        assert config.log.file_level == "DEBUG"
        assert config.log.console_level == "INFO"
        assert config.log.retention == "10 days"
        assert config.log.rotation == "500 MB"
        
        # Test with prod environment specifically
        config = get_config("config.yaml", "prod")
        assert isinstance(config, BaseConfig)
        assert config.app.name == "Auto Database Deployment"
        assert config.db.host == "localhost"
        assert config.redis.host == "localhost"
        assert config.log.file_level == "DEBUG"
        assert config.log.console_level == "WARN"
        assert config.log.retention == "7 days"
        assert config.log.rotation == "1 GB"

    def test_get_config_invalid_env(self):
        """Test get_config function with invalid environment"""
        # This would depend on how you want to handle invalid environments
        # For now, we'll skip implementing this test as it depends on your intended behavior
        pass
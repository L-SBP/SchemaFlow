# backend/app/config/base.py

from typing import List, Optional

from pydantic_settings import BaseSettings
from pydantic import SecretStr, BaseModel
from sqlalchemy import URL

class Appconfig(BaseSettings):
    """
    FastAPI的应用配置
    """
    # 应用名称
    name: str
    # 应用描述
    description: str
    # 应用接口
    api: str
    # 应用主机地址
    host: str
    # 应用端口
    port: int
    # uvicorn应用入口
    uvicorn: str
    # 应用版本
    version: str
    # 是否自动重载
    reload: bool

class DatabaseConfig(BaseSettings):
    """
    PostgresSQL数据库配置
    """

    # 数据库主机地址
    host: str
    # 数据库端口
    port: int
    # 数据库用户名
    username: str
    # 数据库密码
    password: SecretStr
    # 数据库名称
    database: str
    # 数据库连接配置
    driver: str
    # 是否开启sqlalchemy日志
    echo: bool
    # 允许溢出连接池大小的最大连接数
    max_overflow: int
    # 连接池大小
    pool_size: int
    # 池回收连接的时间间隔
    pool_recycle: int
    # 连接池中没有线程可用时，最多等待的时间
    pool_timeout: int

    @property
    def sqlalchemy_database_url(self) -> URL:
        return URL.create(
            drivername=self.driver,
            username=self.username,
            password=self.password.get_secret_value(),
            host=self.host,
            port=self.port,
            database=self.database,
        )


class RedisConfig(BaseSettings):
    """
    Redis数据库配置
    """

    # Redis主机地址
    host: str
    # Redis端口
    port: int
    # Redis数据库索引
    db: int
    # Redis密码
    password: Optional[str] = None
    # 连接超时时间（秒）
    connect_timeout: float = 5.0
    # 读取超时时间（秒）
    read_timeout: float = 3.0
    # 写入超时时间（秒）
    write_timeout: float = 3.0
    # 连接池最大连接数（建议根据实际并发量调整，生产环境通常设置为50-200）
    max_connections: int = 50
    # 订阅频道
    subscribe_channel: str
    # 键前缀（用于多环境隔离）
    key_prefix: str = ""

class LogConfig(BaseSettings):
    """
    日志配置
    """
    # 日志文件级别
    file_level: str
    # 日志控制台级别
    console_level: str
    # 日志保存时间
    retention: str
    # 日志轮转时间
    rotation: str

class JWTConfig(BaseSettings):
    """
    JWT配置
    """
    # JWT密钥
    secret_key: str
    # JWT算法
    algorithm: str
    # JWT过期时间
    token_expire_time_seconds: int

class SMTP(BaseSettings):
    """
    SMTP配置
    """
    # SMTP服务器
    host: str
    # SMTP端口
    port: int
    # 发送者名称
    sender_name: str
    # 发送者邮箱
    sender: str
    # 授权码
    key: str
    # 验证码有效期
    expire_time_seconds: int

class AIConfig(BaseSettings):
    modelscope_api_key: str = "dummy_key"
    mermaid_api_key: str = ""

class MySQLConfig(BaseSettings):
    """
    MySQL数据库配置
    """
    # 数据库主机
    host: str
    # 数据库端口
    port: int
    # 用户名
    username: str
    # 密码
    password: SecretStr
    # 数据库连接驱动
    driver: str
    # SSL
    ssl: bool
    # plugin
    plugin: str
    # sqlalchemy连接池配置
    max_overflow: int
    # sqlalchemy连接池大小
    pool_size: int
    # sqlalchemy连接池回收时间
    pool_recycle: int
    # sqlalchemy连接池空闲时间
    pool_timeout: int

    @property
    def sqlalchemy_database_url(self) -> URL:
        return URL.create(
            drivername=self.driver,
            username=self.username,
            password=self.password.get_secret_value(),
            host=self.host,
            port=self.port
        )

class PostgresConfig(BaseSettings):
    # 数据库主机
    host: str
    # 端口
    port: int
    # 用户名
    username: str
    # 密码
    password: str
    # 数据库连接驱动
    driver: str
    # 显示执行SQL
    echo: bool
    # sqlalchemy连接池配置
    max_overflow: int
    pool_size: int
    pool_recycle: int
    pool_timeout: int

    @property
    def sqlalchemy_database_url(self) -> URL:
        return URL.create(
            drivername=self.driver,
            username=self.username,
            password=self.password,
            host=self.host,
            port=self.port
        )


class SQLiteConfig(BaseSettings):
    # 数据库驱动
    driver: str
    # 数据库文件基础路径
    db_path: str
    # 显示执行SQL
    echo: bool
    # sqlalchemy连接池配置
    max_overflow: int
    pool_size: int
    pool_recycle: int
    pool_timeout: int

    @property
    def sqlalchemy_database_url(self) -> str:
        # SQLite使用文件路径，不需要用户名密码等
        return f"{self.driver}:///{self.db_path}/{{db_name}}.db"

    def get_database_path(self, db_name: str, user_id: Optional[int] = None) -> str:
        """获取数据库文件的完整路径，支持用户隔离
        
        Args:
            db_name: 数据库名称
            user_id: 用户ID，用于隔离不同用户的数据库文件
            
        Returns:
            数据库文件的完整路径
        """
        import os
        from pathlib import Path
        
        if user_id is not None:
            # 为不同用户创建独立的目录
            user_dir = Path(self.db_path) / f"user_{user_id}"
            user_dir.mkdir(parents=True, exist_ok=True)
            return str(user_dir / f"{db_name}.db")
        else:
            # 默认路径（兼容旧代码）
            return str(Path(self.db_path) / f"{db_name}.db")

class UserSQLPermissions(BaseModel):
    allowed_operations: List[str]
    forbidden_operations: List[str]

class SQLPermissions(BaseSettings):
    """
    SQL权限配置
    """
    root: UserSQLPermissions
    normal: UserSQLPermissions


class BaseConfig(BaseSettings):
    """
    基础配置
    """

    # 应用配置
    app: Appconfig
    #  ai 配置！
    ai: AIConfig = AIConfig()
    # PostgresSQL数据库配置
    db: DatabaseConfig
    # Redis配置
    redis: RedisConfig
    # 日志配置
    log: LogConfig
    # JWT配置
    jwt: JWTConfig
    # SMTP配置
    smtp: SMTP

    # 前端基础地址（用于拼接邮件内的密码重置链接）
    frontend_base_url: str = "http://localhost:5173/"

    # 忘记密码/重置密码配置
    password_reset_token_expire_seconds: int = 900
    password_reset_request_limit_per_email_per_hour: int = 3
    password_reset_request_limit_per_ip_per_hour: int = 20
    # MySQL数据库配置
    mysql: MySQLConfig
    # Postgres数据库配置
    postgresql: PostgresConfig
    # SQLite数据库配置
    sqlite: SQLiteConfig
    # SQL权限配置
    sql_permissions: SQLPermissions
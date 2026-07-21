# backend/app/server.py

from pathlib import Path
from dotenv import load_dotenv

# 加载 .env 文件（项目根目录: src/backend/.env）
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(env_path)

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
# 导入第三方库异常类
import redis.exceptions as redis_exceptions
from jose import JWTError
import httpx
import aiohttp
import celery.exceptions as celery_exceptions

from core.config import config
from core.log import log
from core.database import PsqlHelper
from core.exceptions import BusinessException, AppException
from core.exception_handlers import (
    business_exception_handler,
    app_exception_handler,
    validation_exception_handler,
    pydantic_validation_exception_handler,
    sqlalchemy_exception_handler,
    general_exception_handler,
    io_exception_handler,
    timeout_exception_handler,
    type_exception_handler,
    value_exception_handler,
    key_exception_handler,
    jwt_exception_handler,
)

import models
from mysql.mysql_database import MysqlHelper
from postgresql.postgres_database import PostgresHelper
from sqlite.sqlite_database import SQLiteHelper
from redis_client.redis import init_redis, close_redis, get_redis, init_redis_listener, close_redis_listener
from redis_client.expiration_listener import redis_expire_listener
from api.v1.api import api_router
import asyncio
import os

async def startup_services(app: FastAPI):
    """
    初始化服务

    :param app: FastAPI应用程序实例
    """

    # 初始化config
    log.info("initialize config")
    app.state.config = config

    # 初始化数据库连接
    log.info("initialize database linking")
    app.state.psql_engine = await PsqlHelper.init_conn_psql(app.state.config.db)

    # 初始化 LLM 模型注册表（从 ai_model_config 表加载）
    log.info("initialize LLM model registry")
    from core.llm import init_model_registry
    async with PsqlHelper.get_session(app.state.psql_engine) as db:
        await init_model_registry(db)

    # 初始化Mysql连接
    await MysqlHelper.init_root_engine(config.mysql)

    # 测试Mysql连接
    await MysqlHelper.test_connection()

    # 初始化 PostgreSQL Root 连接 (用于用户项目)
    log.info("initialize postgresql root engine")
    await PostgresHelper.init_root_engine(config.postgresql)
    try:
        await PostgresHelper.test_connection()
        log.info("PostgreSQL connection test passed")
    except Exception as e:
        log.error(f"PostgreSQL connection test failed: {e}")

    # 初始化Redis连接
    log.info("initialize redis_client linking")
    await init_redis()
    redis = get_redis()
    if redis :
        app.state.redis = get_redis()
    
    # 初始化Redis监听连接并启动监听器
    log.info("initialize redis_client listener")
    await init_redis_listener()
    # 在后台启动Redis过期事件监听器
    asyncio.create_task(redis_expire_listener())

async def close_services(app: FastAPI):
    """
    关闭服务

    :param app: FastAPI应用程序实例
    """

    # 关闭数据库连接
    log.info("close database linking")
    await PsqlHelper.close_conn_psql(app.state.psql_engine)
    # 关闭 PostgreSQL 连接池 (释放所有用户项目的连接)
    await PostgresHelper.close_all_engine()
    # 关闭 SQLite 连接池 (释放文件句柄)
    await SQLiteHelper.close_all_engine()
    # 关闭Redis连接
    await close_redis()
    # 关闭Redis监听连接
    await close_redis_listener()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用程序生命周期管理器

    :param app: FastAPI应用程序实例
    """

    await startup_services(app)
    log.info("app startup")
    yield
    log.info("app shutdown")
    await close_services(app)

def create_app() -> FastAPI:
    """
    创建FastAPI应用实例
    
    Returns:
        FastAPI: 配置好的FastAPI应用实例
    """
    app = FastAPI(
        title=config.app.name,
        description=config.app.description,
        version=config.app.version,
        lifespan=lifespan,
    )
    
    # 注册异常处理器
    app.add_exception_handler(BusinessException, business_exception_handler)
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValidationError, pydantic_validation_exception_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
    
    # 注册Python内置异常处理器
    app.add_exception_handler(IOError, io_exception_handler)
    app.add_exception_handler(FileNotFoundError, io_exception_handler)
    app.add_exception_handler(TimeoutError, timeout_exception_handler)
    app.add_exception_handler(TypeError, type_exception_handler)
    app.add_exception_handler(ValueError, value_exception_handler)
    app.add_exception_handler(KeyError, key_exception_handler)
    app.add_exception_handler(AttributeError, key_exception_handler)
    
    # 注册第三方库异常处理器
    app.add_exception_handler(JWTError, jwt_exception_handler)
    
    # 兜底异常处理器
    app.add_exception_handler(Exception, general_exception_handler)
    
    # 挂载静态目录
    static_dir = "static"
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    
    # 注册API路由
    app.include_router(api_router, prefix=config.app.api)
    
    return app

# 创建应用实例
my_app = create_app()
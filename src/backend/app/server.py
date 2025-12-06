from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from core.config import config
from core.log import log
from core.database import PsqlHelper
import models
from redis.redis import init_redis, close_redis, get_redis, init_redis_listener, close_redis_listener
from redis.expiration_listener import redis_expire_listener
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

    # 初始化Redis连接
    log.info("initialize redis linking")
    await init_redis()
    redis = get_redis()
    if redis :
        app.state.redis = get_redis()
    
    # 初始化Redis监听连接并启动监听器
    log.info("initialize redis listener")
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

my_app = FastAPI(
    title=config.app.name,
    description=config.app.description,
    version=config.app.version,
    lifespan=lifespan,
)

# ============================================================
# 挂载静态目录 (为了支持文件导出下载)
# ============================================================
# 1. 确保目录存在
static_dir = "static"
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

# 2. 挂载到 /static 路径
# 这意味着：访问 http://host:port/static/xxx 就会去读取项目根目录 static/xxx 文件
my_app.mount("/static", StaticFiles(directory=static_dir), name="static")

my_app.include_router(api_router, prefix=config.app.api)
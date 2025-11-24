from contextlib import asynccontextmanager

from fastapi import FastAPI

from core.config import config
from core.log import log
from core.database import PsqlHelper
from api.v1.api import api_router

async def startup_services(app: FastAPI):
    """
    初始化服务

    :param app: FastAPI应用程序实例
    """

    # 初始化config
    app.state.config = config
    # 初始化数据库连接
    log.info("initialize database linking")
    app.state.psql_engine = await PsqlHelper.init_conn_psql(app.state.config.db)

async def close_services(app: FastAPI):
    """
    关闭服务

    :param app: FastAPI应用程序实例
    """

    # 关闭数据库连接
    log.info("close database linking")
    await PsqlHelper.close_conn_psql(app.state.psql_engine)

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

my_app.include_router(api_router, prefix=config.app.api)

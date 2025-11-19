from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import get_config
from app.core.database import PsqlHelper

config = get_config()

async def startup_services(app: FastAPI):
    """
    初始化服务

    :param app: FastAPI应用程序实例
    """

    # 初始化config
    app.state.config = config
    # 初始化数据库连接
    app.state.psql_engine = await PsqlHelper.init_conn_psql(app.state.config.db)

async def close_services(app: FastAPI):
    """
    关闭服务

    :param app: FastAPI应用程序实例
    """

    # 关闭数据库连接
    await PsqlHelper.close_conn_psql(app.state.psql_engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用程序生命周期管理器

    :param app: FastAPI应用程序实例
    """

    await startup_services(app)
    yield
    await close_services(app)

app = FastAPI(
    title=config.app.name,
    description=config.app.description,
    version=config.app.version,
    lifespan=lifespan,
)
"""
Redis 过期事件处理。

于无请求上下文下处理 Token 过期，构造会话并调用登出逻辑。
"""

# backend/app/service/redis_expire_handle_service.py

from core.database import PsqlHelper
from service.user_service import service_logout
from core.config import config
from core.log import log

async def service_handle_expire_token(token: str) -> None:
    """
    处理过期的 Token（无请求上下文）。

    直接创建数据库会话以响应 Redis 过期事件，并触发登出逻辑。

    Args:
        token (str): 过期的 Token。

    Returns:
        None: 无返回值。

    Raises:
        Exception: 登出或资源清理过程中出现的异常会被记录并吞并。
    """
    log.info(f"Handling expired token: {token}")
    
    # 虽然这样不好，但是这里没有request对象，只能这样处理，不然结构就要大改
    db_engine = PsqlHelper._get_async_engine(config.db)
    db_session = PsqlHelper._get_async_session(db_engine)
    
    try:
        # Process the logout with the directly created session
        await service_logout(db_session, token)
        log.info(f"Successfully handled expired token: {token}")
    except Exception as e:
        log.error(f"Error handling expired token {token}: {e}")
    finally:
        # Ensure the session is closed
        await db_session.close()
        await db_engine.dispose()

from sqlalchemy.ext.asyncio import AsyncSession
from core.database import PsqlHelper
from service.user_service import service_logout
from core.config import config
from core.log import log

async def service_handle_expire_token(token: str):
    """
    Handle expired token without request context.
    Creates a database session directly since this is triggered by Redis expiration events.
    
    Args:
        token (str): The expired token to handle
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
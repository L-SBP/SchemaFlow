import asyncio
import aioredis

from aioredis.client import PubSub

from service.redis_expire_handle_service import service_handle_expire_token
from core.log import log
from core.config import config

async def redis_expire_handler(expire_key):
    """
    过期redis key 分发
    :param expire_key:
    :return:
    """
    log.info(f"Expired key received: {expire_key}")
    if expire_key.startswith("verification:"):
        log.info(f"Verification code expired: {expire_key}")
    elif expire_key.startswith("token:"):
        token = expire_key[len("token:"):]  # Fixed extraction
        log.info(f"Token expired: {token}")
        await service_handle_expire_token(token)  # Added await


async def redis_expire_listener():
    """
    监听channel，等待过期事件，将过期事件交给分发逻辑处理后续动作
    :return:
    """
    # Create a separate Redis connection for listening
    redis_conn = aioredis.from_url(
        f"redis://{config.redis.host}:{config.redis.port}",
        password=config.redis.password,
        db=config.redis.db,
        encoding="utf-8",
        decode_responses=True
    )
    
    try:
        # Enable keyspace notifications for expired events
        await redis_conn.config_set("notify-keyspace-events", "Ex")
        
        pubsub = redis_conn.pubsub()
        # Use the correct pattern for key expiration events
        await pubsub.psubscribe("__keyevent@*__:expired")
        
        log.info("Redis expiration listener started, waiting for events...")
        
        while True:
            try:
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message:
                    log.info(f"Received message: {message}")
                    expire_key = message["data"]
                    log.info(f"Processing expired key: {expire_key}")
                    asyncio.create_task(redis_expire_handler(expire_key))
            except Exception as e:
                log.error(f"Error in Redis expire listener: {e}")
                await asyncio.sleep(3)
                
    except Exception as e:
        log.error(f"Failed to start Redis expiration listener: {e}")
    finally:
        try:
            await redis_conn.aclose()
        except:
            pass
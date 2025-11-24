import aioredis
import asyncio

from core.config import config
from core.log import log

redis = None

async def init_redis():
    global redis
    # Use the newer connection method for aioredis
    redis = aioredis.from_url(
        f"redis://{config.redis.host}:{config.redis.port}",
        password=config.redis.password,
        db=config.redis.db,
        encoding="utf-8",
        decode_responses=True
    )
    try:
        await redis.ping()
        log.info("Connected to Redis")
    except Exception as e:
        log.error(f"Failed to connect to Redis: {e}")

def get_redis():
    global redis

    if not redis:
        log.warning("Redis is not initialized")
        return None
    return redis

async def close_redis():
    global redis
    if redis:
        try:
            await redis.aclose()
            log.info("Closed Redis connection")
        except Exception as e:
            log.error(f"Failed to close Redis connection: {e}")
        finally:
            redis = None
import aioredis

from core.config import config
from core.log import log

redis = None
redis_listener = None

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

async def init_redis_listener():
    """
    Initialize Redis listener for key expiration events.
    This requires a separate connection as per Redis limitations.
    """
    global redis_listener
    # Create a separate connection for listening to events
    redis_listener = aioredis.from_url(
        f"redis://{config.redis.host}:{config.redis.port}",
        password=config.redis.password,
        db=config.redis.db,
        encoding="utf-8",
        decode_responses=True
    )
    
    try:
        # Enable keyspace notifications for expired events
        await redis_listener.config_set("notify-keyspace-events", "Ex")
        await redis_listener.ping()
        log.info("Connected to Redis listener")
    except Exception as e:
        log.error(f"Failed to connect to Redis listener: {e}")

def get_redis():
    global redis

    if not redis:
        log.warning("Redis is not initialized")
        return None
    return redis

def get_redis_listener():
    """
    Get the Redis listener connection.
    """
    global redis_listener
    
    if not redis_listener:
        log.warning("Redis listener is not initialized")
        return None
    return redis_listener

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

async def close_redis_listener():
    """
    Close the Redis listener connection.
    """
    global redis_listener
    if redis_listener:
        try:
            await redis_listener.aclose()
            log.info("Closed Redis listener connection")
        except Exception as e:
            log.error(f"Failed to close Redis listener connection: {e}")
        finally:
            redis_listener = None
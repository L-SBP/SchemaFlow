"""
Redis 连接管理器。

本模块负责创建和管理 Redis 连接池，提供全局的 Redis 客户端实例。
支持常规数据操作连接和 Pub/Sub 监听专用连接的独立管理。
"""

# backend/app/redis_client/redis_client.py

import aioredis

from core.config import config
from core.log import log

redis = None
redis_listener = None

async def init_redis():
    """
    初始化 Redis 连接池。

    创建一个全局的 Redis 连接池实例，用于常规的数据读写操作。
    配置参数（Host, Port, DB）从全局配置中读取。
    """
    global redis
    # Use the newer connection method for aioredis
    redis = aioredis.from_url(
        f"redis://{config.redis.host}:{config.redis.port}",
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
    初始化 Redis 监听器专用连接。

    由于 Redis 的 Pub/Sub（发布订阅）模式和阻塞命令需要独占连接，
    因此单独创建一个连接实例用于监听键过期等事件。
    """
    global redis_listener
    # Create a separate connection for listening to events
    redis_listener = aioredis.from_url(
        f"redis://{config.redis.host}:{config.redis.port}",
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
    """
    获取全局 Redis 客户端实例。

    Returns:
        aioredis.Redis: Redis 客户端实例。如果未初始化则返回 None。
    """
    global redis

    if not redis:
        log.warning("Redis is not initialized")
        return None
    return redis

def get_redis_listener():
    """
    获取 Redis 监听器专用连接实例。

    Returns:
        aioredis.Redis: 监听器专用的 Redis 连接实例。
    """
    global redis_listener
    
    if not redis_listener:
        log.warning("Redis listener is not initialized")
        return None
    return redis_listener

async def close_redis():
    """
    关闭 Redis 连接池。

    释放常规操作的 Redis 连接资源。
    """
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
    关闭 Redis 监听器连接。

    释放用于事件监听的专用 Redis 连接资源。
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
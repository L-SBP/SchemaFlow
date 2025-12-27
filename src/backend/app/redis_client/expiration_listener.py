"""
Redis 过期事件监听器。

本模块实现了对 Redis 键过期事件 (expired events) 的监听和处理机制。
主要用于处理 Token 过期、验证码失效等需要触发后续业务逻辑的场景。
"""

# backend/app/redis_client/expiration_listener.py

import asyncio
import aioredis

from aioredis.client import PubSub

from service.redis_expire_handle_service import service_handle_expire_token
from redis_client.redis_keys import redis_key_manager
from core.log import log
from core.config import config

async def redis_expire_handler(expire_key: str):
    """
    Redis 过期键事件分发处理器。

    根据过期键的前缀将事件分发给对应的业务逻辑处理。

    Args:
        expire_key (str): 已过期的 Redis 键名。
    """
    log.info(f"Expired key received: {expire_key}")
    
    # 获取基础前缀（用于环境隔离）
    base_prefix = redis_key_manager._get_base_prefix()
    prefix_len = len(base_prefix) + 1 if base_prefix else 0
    
    # 提取实际键名（去除基础前缀）
    actual_key = expire_key[prefix_len:] if base_prefix else expire_key
    
    verification_prefix = redis_key_manager.VERIFICATION_PREFIX
    token_prefix = redis_key_manager.TOKEN_PREFIX
    
    if actual_key.startswith(f"{verification_prefix}:"):
        log.info(f"Verification code expired: {expire_key}")
    elif actual_key.startswith(f"{token_prefix}:"):
        token = actual_key[len(f"{token_prefix}:"):]
        log.info(f"Token expired: {token}")
        await service_handle_expire_token(token)  # Added await


async def redis_expire_listener():
    """
    启动 Redis 过期事件监听循环。

    建立一个独立的 Redis 连接，订阅 `__keyevent@*__:expired` 频道，
    实时监听所有数据库的键过期事件，并将其投递给 `redis_expire_handler` 进行处理。
    此函数会无限循环运行，直到程序退出。
    """
    # Create a separate Redis connection for listening
    redis_conn = aioredis.from_url(
        f"redis://{config.redis.host}:{config.redis.port}/{config.redis.db}",
        password=config.redis.password,
        encoding="utf-8",
        decode_responses=True,
        connect_timeout=config.redis.connect_timeout,
        read_timeout=config.redis.read_timeout,
        write_timeout=config.redis.write_timeout
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
        log.error(f"无法启动Redis过期监听器: {e}")
    finally:
        try:
            await redis_conn.aclose()
        except:
            pass
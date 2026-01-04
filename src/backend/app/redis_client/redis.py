"""
Redis 连接管理器。

本模块负责创建和管理 Redis 连接池，提供全局的 Redis 客户端实例。
支持常规数据操作连接和 Pub/Sub 监听专用连接的独立管理。
"""

# backend/app/redis_client/redis_client.py

import aioredis
import asyncio

from core.config import config
from core.log import log

redis = None
redis_listener = None

async def init_redis():
    """
    初始化 Redis 连接池。

    创建一个全局的 Redis 连接池实例，用于常规的数据读写操作。
    配置参数从全局配置中读取，支持密码、超时、连接池、哨兵模式和SSL设置。
    """
    global redis
    
    try:
        # 根据配置选择连接方式
        if config.redis.sentinel_enabled:
            # 哨兵模式连接
            sentinel_kwargs = {
                'sentinels': [(host, int(port)) for host, port in (s.split(':') for s in config.redis.sentinels)],
                'sentinel_kwargs': {
                    'password': config.redis.password,
                    'socket_connect_timeout': config.redis.connect_timeout,
                    'socket_timeout': config.redis.read_timeout,
                },
                'encoding': 'utf-8',
                'decode_responses': True,
                'socket_connect_timeout': config.redis.connect_timeout,
                'socket_timeout': config.redis.read_timeout,
                'max_connections': config.redis.max_connections,
                'retry_on_timeout': True,
                'health_check_interval': config.redis.health_check_interval
            }
            
            # 创建哨兵客户端
            sentinel = aioredis.sentinel.Sentinel(
                sentinel_kwargs['sentinels'],
                sentinel_kwargs['sentinel_kwargs'],
                encoding=sentinel_kwargs['encoding'],
                decode_responses=sentinel_kwargs['decode_responses']
            )
            
            # 获取主节点连接
            redis = sentinel.master_for(
                config.redis.master_name,
                db=config.redis.db,
                socket_connect_timeout=sentinel_kwargs['socket_connect_timeout'],
                socket_timeout=sentinel_kwargs['socket_timeout'],
                max_connections=sentinel_kwargs['max_connections'],
                retry_on_timeout=sentinel_kwargs['retry_on_timeout'],
                health_check_interval=sentinel_kwargs['health_check_interval']
            )
        else:
            # 单节点连接
            redis_url = f"redis://{config.redis.host}:{config.redis.port}/{config.redis.db}"
            
            # 构建连接参数
            connection_kwargs = {
                "encoding": "utf-8",
                "decode_responses": True,
                "socket_connect_timeout": config.redis.connect_timeout,
                "socket_timeout": config.redis.read_timeout,  # For aioredis 2.x
                "max_connections": config.redis.max_connections,
                "retry_on_timeout": True,
                "health_check_interval": config.redis.health_check_interval
            }
            
            # 仅当设置了密码时才添加密码参数
            if config.redis.password:
                connection_kwargs["password"] = config.redis.password
            
            # 仅当启用SSL时添加SSL参数
            if config.redis.ssl:
                connection_kwargs["ssl"] = config.redis.ssl
                connection_kwargs["ssl_cert_reqs"] = config.redis.ssl_cert_reqs
            
            redis = aioredis.from_url(
                redis_url,
                **connection_kwargs
            )
        
        await redis.ping()
        log.info("Connected to Redis")
    except Exception as e:
        log.error(f"无法连接到Redis: {e}")
        # 实现连接重试
        retry_count = 0
        while retry_count < config.redis.max_retries:
            try:
                retry_count += 1
                log.info(f"第{retry_count}次重试连接Redis...")
                await asyncio.sleep(config.redis.retry_interval)
                
                if config.redis.sentinel_enabled:
                    sentinel = aioredis.sentinel.Sentinel(
                        [(host, int(port)) for host, port in (s.split(':') for s in config.redis.sentinels)],
                        sentinel_kwargs={'password': config.redis.password},
                        encoding='utf-8',
                        decode_responses=True
                    )
                    redis = sentinel.master_for(config.redis.master_name, db=config.redis.db)
                else:
                    redis_url = f"redis://{config.redis.host}:{config.redis.port}/{config.redis.db}"
                    redis = aioredis.from_url(
                        redis_url,
                        password=config.redis.password,
                        encoding="utf-8",
                        decode_responses=True,
                        socket_connect_timeout=config.redis.connect_timeout,
                        socket_timeout=config.redis.read_timeout  # For aioredis 2.x
                    )
                
                await redis.ping()
                log.info(f"第{retry_count}次重试连接Redis成功")
                break
            except Exception as retry_e:
                log.error(f"第{retry_count}次重试连接Redis失败: {retry_e}")
                if retry_count == config.redis.max_retries:
                    log.error(f"已达到最大重试次数({config.redis.max_retries})，无法连接到Redis")

async def init_redis_listener():
    """
    初始化 Redis 监听器专用连接。

    由于 Redis 的 Pub/Sub（发布订阅）模式和阻塞命令需要独占连接，
    因此单独创建一个连接实例用于监听键过期等事件。
    """
    global redis_listener
    # 构建 Redis URL
    url = f"redis://{config.redis.host}:{config.redis.port}/{config.redis.db}"
    
    # Create a separate connection for listening to events
    redis_listener = aioredis.from_url(
        url,
        password=config.redis.password,
        encoding="utf-8",
        decode_responses=True,
        socket_connect_timeout=config.redis.connect_timeout,
        socket_timeout=config.redis.read_timeout,  # For aioredis 2.x
        max_connections=1  # 监听器只需要一个连接
    )
    
    try:
        # Enable keyspace notifications for expired events
        await redis_listener.config_set("notify-keyspace-events", "Ex")
        await redis_listener.ping()
        log.info("Connected to Redis listener")
    except Exception as e:
        log.error(f"无法连接到Redis监听器: {e}")

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
            await redis.close()
            log.info("Closed Redis connection")
        except Exception as e:
            log.error(f"无法关闭Redis连接: {e}")
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
            await redis_listener.close()
            log.info("Closed Redis listener connection")
        except Exception as e:
            log.error(f"无法关闭Redis监听器连接: {e}")
        finally:
            redis_listener = None